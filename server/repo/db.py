import datetime
from typing import AsyncIterator, overload

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import models as db_models
from ..models.game import (
    Game,
    GamePlayer,
    GameResult,
    NewGameResult,
    PlayerExtraScore,
    PlayerResult,
)
from ..models.player import Player
from ..models.tournament import Table, Tournament
from ..models.user import User
from ..utils.datetime_utils import get_current_datetime_utc
from ..utils.exceptions.repo import (
    InvalidPasswordError,
    PlayerAlreadyExistsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ..utils.security import password_context
from .base import BaseRepo

type WithID[T] = tuple[str, T]
SQLDefault = text("DEFAULT")


class UsersRepo(BaseRepo[AsyncSession]):
    @overload
    async def _db_to_model(self, db_user: None, db_player: db_models.Player | None = None) -> None:
        pass

    @overload
    async def _db_to_model(
        self,
        db_user: db_models.User,
        db_player: db_models.Player | None = None,
    ) -> User:
        pass

    async def _db_to_model(
        self,
        db_user: db_models.User | None,
        db_player: db_models.Player | None = None,
    ) -> User | None:
        if db_user is None:
            return None
        if db_player is None:
            players = PlayersRepo(self._conn)
            db_player = await players.get_by_id(db_user.player_id)
        return User(
            username=db_user.username,
            nickname=db_player.nickname,
            real_name=db_player.real_name,
        )

    async def get_by_id(self, user_id: str) -> User | None:
        return await self._db_to_model(await self._conn.get(db_models.User, user_id))

    async def get_by_username(self, username: str) -> User | None:
        query = select(db_models.User).where(db_models.User.username == username)
        res = (await self._conn.execute(query)).scalar_one_or_none()
        return await self._db_to_model(res)

    async def _verify_password(self, user: db_models.User, password: str) -> bool:
        is_valid, new_hash = password_context.verify_and_update(password, user.password_hash)
        if not is_valid:
            return False
        if new_hash is not None:
            await self._conn.execute(
                update(db_models.User)
                .where(db_models.User.id == user.id)
                .values(password_hash=new_hash)
            )
        return True

    async def verify_password(self, user_id: str, password: str) -> bool:
        user: User | None = await self._conn.get(db_models.User, user_id)
        if user is None:
            return False
        return await self._verify_password(user, password)

    async def try_login(self, username: str, password: str) -> WithID[User]:
        """Try to log in with the given username and password.

        Args:
            username: The username of the user.
            password: The password of the user.

        Returns:
            A tuple containing the user ID and the user.

        Raises:
            UserNotFoundError: If a user with the given username does not exist.
            InvalidPasswordError: If the password is incorrect.
        """
        query = select(db_models.User).where(db_models.User.username == username)
        user = (await self._conn.execute(query)).scalar_one_or_none()
        if user is None:
            raise UserNotFoundError(username)
        is_valid = await self._verify_password(user, password)
        if not is_valid:
            raise InvalidPasswordError()
        return user.id, await self._db_to_model(user)

    async def create(
        self,
        username: str,
        password: str,
        *,
        nickname: str,
        real_name: str,
    ) -> User:
        """Create a new user and a player with the given nickname.

        Args:
            username: The username of the new user.
            password: The password of the new user.
            nickname: The nickname of the new player.
            real_name: The real name of the new player.

        Returns:
            The created user.

        Raises:
            UserAlreadyExistsError: If a user with the given username already exists.
            PlayerAlreadyExistsError: If a player with the given nickname already exists.
        """
        players = PlayersRepo(self._conn)
        player = await players.edit_or_create(nickname, real_name=real_name, id_=None)
        return await self.create_linked(
            username=username,
            password=password,
            player_id=str(player.id),
        )

    async def create_linked(
        self,
        username: str,
        password: str,
        *,
        player_id: str,
    ) -> User:
        """Create a new user linked with an existing player.

        Args:
            username: The username of the new user.
            password: The password of the new user.
            player_id: The ID of the existing player.

        Returns:
            The created user.

        Raises:
            UserAlreadyExistsError: If a user with the given username already exists.
            PlayerAlreadyExistsError: If a player with the given nickname already exists.
        """
        players = PlayersRepo(self._conn)
        player = await players.get_by_id(player_id)
        password_hash = password_context.hash(password)
        query = (
            insert(db_models.User)
            .values(username=username, password_hash=password_hash, player_id=player.id)
            .returning(db_models.User)
        )
        try:
            result = await self._conn.execute(query)
        except IntegrityError as e:
            raise UserAlreadyExistsError(username) from e
        user = result.scalar_one()
        return await self._db_to_model(user, player)

    async def edit_password(self, user_id: str, password: str) -> None:
        password_hash = password_context.hash(password)
        await self._conn.execute(
            update(db_models.User)
            .where(db_models.User.id == user_id)
            .values(password_hash=password_hash)
        )


class PlayersRepo(BaseRepo[AsyncSession]):
    @staticmethod
    def _db_to_model(db_player: db_models.Player | None) -> Player | None:
        if db_player is None:
            return None
        return Player(
            id=db_player.id,
            nickname=db_player.nickname,
            real_name=db_player.real_name,
        )

    async def get_by_id(self, player_id: str) -> Player | None:
        return self._db_to_model(await self._conn.get(db_models.Player, player_id))

    async def get_by_nickname(self, nickname: str) -> Player | None:
        query = select(db_models.Player).where(db_models.Player.nickname == nickname)
        res = (await self._conn.execute(query)).scalar_one_or_none()
        return self._db_to_model(res)

    async def get_all(self) -> list[Player]:
        query = select(db_models.Player)
        return [self._db_to_model(p) for p in (await self._conn.execute(query)).scalars().all()]

    async def get_all_as_stream(self) -> AsyncIterator[Player]:
        query = select(db_models.Player).order_by(db_models.Player.id)
        async for player in await self._conn.stream_scalars(query):
            yield self._db_to_model(player)

    async def count_all(self) -> int:
        query = select(func.count()).select_from(db_models.Player)
        return (await self._conn.execute(query)).scalar()

    async def edit_or_create(
        self,
        nickname: str,
        *,
        real_name: str,
        id_: str | None,
    ) -> Player:
        query = (
            insert(db_models.Player)
            .values(
                nickname=nickname,
                real_name=real_name,
                id=id_ if id_ is not None else SQLDefault,
            )
            .on_conflict_do_update(
                index_elements=[db_models.Player.id],
                set_=dict(nickname=nickname, real_name=real_name),
            )
            .returning(db_models.Player)
        )
        try:
            result = await self._conn.execute(query)
        except IntegrityError as e:
            raise PlayerAlreadyExistsError(nickname) from e
        return self._db_to_model(result.scalar_one())

    async def delete(self, player_id: str) -> None:
        await self._conn.execute(delete(db_models.Player).where(db_models.Player.id == player_id))


class TournamentsRepo(BaseRepo[AsyncSession]):
    @staticmethod
    def _db_to_model(db_tournament: db_models.Tournament | None) -> Tournament | None:
        if db_tournament is None:
            return None
        return Tournament(
            id=db_tournament.id,
            name=db_tournament.name,
            date_from=db_tournament.date_from,
            date_to=db_tournament.date_to,
        )

    async def get_by_id(self, tournament_id: str) -> Tournament | None:
        return self._db_to_model(await self._conn.get(db_models.Tournament, tournament_id))

    async def get_all(self) -> list[Tournament]:
        query = select(db_models.Tournament)
        return [self._db_to_model(t) for t in (await self._conn.execute(query)).scalars().all()]

    async def get_all_as_stream(self) -> AsyncIterator[Tournament]:
        query = select(db_models.Tournament).order_by(db_models.Tournament.id)
        async for tournament in await self._conn.stream_scalars(query):
            yield self._db_to_model(tournament)

    async def get_by_creator_user_id(self, creator_user_id: str) -> list[Tournament]:
        query = select(db_models.Tournament).where(
            db_models.Tournament.created_by_user_id == creator_user_id
        )
        return [self._db_to_model(t) for t in (await self._conn.execute(query)).scalars().all()]

    async def get_by_creator_user_id_as_stream(
        self,
        creator_user_id: str,
    ) -> AsyncIterator[Tournament]:
        query = select(db_models.Tournament).where(
            db_models.Tournament.created_by_user_id == creator_user_id
        )
        async for tournament in await self._conn.stream_scalars(query):
            yield self._db_to_model(tournament)

    async def create(
        self,
        name: str,
        *,
        created_by: str,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
    ) -> Tournament:
        query = (
            insert(db_models.Tournament)
            .values(name=name, date_from=date_from, date_to=date_to, created_by_user_id=created_by)
            .returning(db_models.Tournament)
        )
        result = await self._conn.execute(query)
        return self._db_to_model(result.scalar_one())

    async def edit_name(self, tournament_id: str, name: str) -> None:
        await self._conn.execute(
            update(db_models.Tournament)
            .where(db_models.Tournament.id == tournament_id)
            .values(name=name)
        )

    async def edit_date_from(self, tournament_id: str, date_from: datetime.datetime) -> None:
        await self._conn.execute(
            update(db_models.Tournament)
            .where(db_models.Tournament.id == tournament_id)
            .values(date_from=date_from)
        )

    async def edit_date_to(self, tournament_id: str, date_to: datetime.datetime) -> None:
        await self._conn.execute(
            update(db_models.Tournament)
            .where(db_models.Tournament.id == tournament_id)
            .values(date_to=date_to)
        )


class TablesRepo(BaseRepo[AsyncSession]):
    async def _db_to_model(
        self,
        db_table: db_models.Table | None,
        judge_nickname: str | None = None,
    ) -> Table | None:
        if db_table is None:
            return None
        if judge_nickname is None:
            query = select(db_models.Player).where(db_models.Player.id == db_table.judge_id)
            judge_player = (await self._conn.execute(query)).scalar_one()
            judge_nickname = judge_player.nickname
        return Table(
            id=db_table.id,
            number=db_table.number,
            judge_nickname=judge_nickname,
        )

    async def get_by_id(self, table_id: str) -> Table | None:
        return await self._db_to_model(await self._conn.get(db_models.Table, table_id))

    async def get_by_tournament(self, tournament_id: str) -> list[Table]:
        query = select(db_models.Table).where(db_models.Table.tournament_id == tournament_id)
        return [
            await self._db_to_model(table)
            for table in (await self._conn.execute(query)).scalars().all()
        ]

    async def get_by_tournament_as_stream(self, tournament_id: str) -> AsyncIterator[Table]:
        query = select(db_models.Table).where(db_models.Table.tournament_id == tournament_id)
        async for table in await self._conn.stream_scalars(query):
            yield await self._db_to_model(table)

    async def create(self, tournament_id: str, *, judge_username: str) -> Table:
        judge_query = select(db_models.User).where(db_models.User.username == judge_username)
        judge = (await self._conn.execute(judge_query)).scalar_one()
        last_number_query = select(func.max(db_models.Table.number)).where(
            db_models.Table.tournament_id == tournament_id
        )
        last_number = (await self._conn.execute(last_number_query)).scalar()
        if not last_number:
            last_number = 0
        query = (
            insert(db_models.Table)
            .values(tournament_id=tournament_id, judge_id=judge.player_id, number=last_number + 1)
            .returning(db_models.Table)
        )
        res = (await self._conn.execute(query)).scalar_one()
        return await self._db_to_model(res, judge_username)

    async def delete(self, table_id: str) -> None:
        await self._conn.execute(delete(db_models.Table).where(db_models.Table.id == table_id))


class GamesRepo(BaseRepo[AsyncSession]):
    async def _db_to_model(
        self,
        db_game: db_models.Game | None,
        players: list[GamePlayer] | None = None,
    ) -> Game | None:
        if db_game is None:
            return None
        if players is None:
            query = (
                select(db_models.Player.nickname, db_models.GamePlayer.role)
                .join(db_models.GamePlayer)
                .where(db_models.GamePlayer.game_id == db_game.id)
                .order_by(db_models.GamePlayer.seat)
            )
            players = [
                GamePlayer(nickname=nickname, role=role)
                for nickname, role in await self._conn.execute(query)
            ]
        return Game(
            id=db_game.id,
            number=db_game.number,
            players=players,
            table_id=db_game.table_id,
        )

    async def _db_result_to_model(
        self,
        db_game_result: db_models.GameResult | None,
        player_results: list[PlayerResult] | None = None,
    ) -> GameResult | None:
        if db_game_result is None:
            return None
        if player_results is None:
            query = (
                select(db_models.GamePlayerResult)
                .join(
                    db_models.GamePlayer,
                    (db_models.GamePlayer.player_id == db_models.GamePlayerResult.player_id)
                    & (db_models.GamePlayer.game_id == db_models.GamePlayerResult.game_id),
                )
                .where(db_models.GamePlayerResult.game_id == db_game_result.game_id)
                .order_by(db_models.GamePlayer.seat)
            )
            q_score = select(db_models.GamePlayerExtraScore).where(
                db_models.GamePlayerExtraScore.game_id == db_game_result.game_id
            )
            player_results = [
                PlayerResult(
                    warn_count=item.warn_count,
                    was_kicked=item.was_kicked,
                    caused_other_team_won=item.caused_other_team_won,
                    found_mafia_count=item.found_mafia_count,
                    has_found_sheriff=item.has_found_sheriff,
                    was_killed_first_night=item.was_killed_first_night,
                    guessed_mafia_count=item.guessed_mafia_count,
                    extra_scores=[
                        PlayerExtraScore(points=score.score, reason=score.reason)
                        for score in (
                            await self._conn.execute(
                                q_score.where(
                                    db_models.GamePlayerExtraScore.player_id == item.player_id
                                )
                            )
                        )
                        .scalars()
                        .all()
                    ],
                )
                for item in (await self._conn.execute(query)).scalars()
            ]
        return GameResult(
            winner=db_game_result.winner,
            results=player_results,
            finished_at=db_game_result.finished_at,
        )

    async def get_by_id(self, game_id: str) -> Game | None:
        return await self._db_to_model(await self._conn.get(db_models.Game, game_id))

    async def get_by_table(
        self,
        table_id: str,
        *,
        played_from: datetime.datetime | None = None,
        played_to: datetime.datetime | None = None,
    ) -> list[Game]:
        query = select(db_models.Game).where(db_models.Game.table_id == table_id)
        if played_from is not None or played_to is not None:
            query = query.join(db_models.GameResult)
        if played_from is not None:
            query = query.where(db_models.GameResult.finished_at >= played_from)
        if played_to is not None:
            query = query.where(db_models.GameResult.finished_at <= played_to)
        return [
            await self._db_to_model(game)
            for game in (await self._conn.execute(query)).scalars().all()
        ]

    async def get_by_table_as_stream(
        self,
        table_id: str,
        *,
        played_from: datetime.datetime | None = None,
        played_to: datetime.datetime | None = None,
    ) -> AsyncIterator[Game]:
        query = select(db_models.Game).where(db_models.Game.table_id == table_id)
        if played_from is not None or played_to is not None:
            query = query.join(db_models.GameResult)
        if played_from is not None:
            query = query.where(db_models.GameResult.finished_at >= played_from)
        if played_to is not None:
            query = query.where(db_models.GameResult.finished_at <= played_to)
        async for game in await self._conn.stream_scalars(query):
            yield await self._db_to_model(game)

    async def create(
        self,
        table_id: str,
        *,
        players: list[GamePlayer],
        id_: str | None = None,
    ) -> Game:
        last_number_query = select(func.max(db_models.Game.number)).where(
            db_models.Game.table_id == table_id
        )
        last_number = (await self._conn.execute(last_number_query)).scalar()
        if not last_number:
            last_number = 0
        query = (
            insert(db_models.Game)
            .values(
                table_id=table_id,
                number=last_number + 1,
                id=id_ if id_ is not None else SQLDefault,
            )
            .returning(db_models.Game)
        )
        res = (await self._conn.execute(query)).scalar_one()
        game_id = res.id
        players_repo = PlayersRepo(self._conn)
        for seat, player in enumerate(players, start=1):
            player_id = (await players_repo.get_by_nickname(player.nickname)).id
            await self._conn.execute(
                insert(db_models.GamePlayer)
                .values(game_id=game_id, player_id=player_id, role=player.role, seat=seat)
                .returning(db_models.GamePlayer)
            )
        return await self._db_to_model(res, players)

    async def get_result(self, game_id: str) -> GameResult | None:
        query = select(db_models.GameResult).where(db_models.GameResult.game_id == game_id)
        return await self._db_result_to_model(
            (await self._conn.execute(query)).scalar_one_or_none()
        )

    async def set_result(self, game_id: str, result: NewGameResult) -> GameResult:
        finished_at = (
            result.finished_at if result.finished_at is not None else get_current_datetime_utc()
        )
        query = (
            insert(db_models.GameResult)
            .values(
                game_id=game_id,
                winner=result.winner,
                finished_at=finished_at,
            )
            .returning(db_models.GameResult)
        )
        db_result = (await self._conn.execute(query)).scalar_one()
        game = await self.get_by_id(game_id)
        for player_result, game_player in zip(result.results, game.players):
            player = await PlayersRepo(self._conn).get_by_nickname(game_player.nickname)
            query = insert(db_models.GamePlayerResult).values(
                game_id=game_id,
                player_id=player.id,
                warn_count=player_result.warn_count,
                was_kicked=player_result.was_kicked,
                caused_other_team_won=player_result.caused_other_team_won,
                found_mafia_count=player_result.found_mafia_count,
                has_found_sheriff=player_result.has_found_sheriff,
                was_killed_first_night=player_result.was_killed_first_night,
                guessed_mafia_count=player_result.guessed_mafia_count,
            )
            await self._conn.execute(query)
            for extra_score in player_result.extra_scores:
                await self._conn.execute(
                    insert(db_models.GamePlayerExtraScore).values(
                        game_id=game_id,
                        player_id=player.id,
                        score=extra_score.points,
                        reason=extra_score.reason,
                    )
                )
        if result.raw_game_log is not None:
            await self._conn.execute(
                insert(db_models.GameLog).values(game_id=game_id, raw_game_log=result.raw_game_log)
            )
        return await self._db_result_to_model(db_result, result.results)
