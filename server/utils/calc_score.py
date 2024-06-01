import dataclasses
from typing import Any

from ..models.game import Game, GamePlayer, GameResult, PlayerResult
from ..models.score import ScoreRow


@dataclasses.dataclass(kw_only=True)
class TournamentGame:
    game: Game
    result: GameResult


def _sort_key(item: ScoreRow) -> Any:
    return -item.sum, -item.play_count, -item.win_rate, item.nickname


def calc_score(games: list[TournamentGame]) -> list[ScoreRow]:
    players = {}
    for game in games:
        player: GamePlayer
        result: PlayerResult
        for player, result in zip(game.game.players, game.result.results):
            row = players.setdefault(player.nickname, ScoreRow(nickname=player.nickname))
            row.games_by_role[player.role] += 1
            if result.was_killed_first_night:
                row.first_night_killed_times += 1
                if result.guessed_mafia_count == 2:
                    row.best_turn_points += 0.25
                elif result.guessed_mafia_count == 3:
                    row.best_turn_points += 0.5
            if game.result.winner == player.role.team:
                row.wins_by_role[player.role] += 1
            # TODO: calc Ci points
            row.judge_extra_points += sum(
                extra.points for extra in result.extra_scores if extra.points > 0
            )
            row.judge_penalty_points += sum(
                extra.points for extra in result.extra_scores if extra.points < 0
            )
            row.warns += result.warn_count
            row.times_kicked += result.was_kicked
            row.times_caused_other_team_won += result.caused_other_team_won
            row.found_mafia_count += result.found_mafia_count
            row.times_found_sheriff += result.has_found_sheriff
            row.times_killed_first_night += result.was_killed_first_night
            if result.was_killed_first_night:
                row.guessed_mafia_counts[result.guessed_mafia_count] += 1
    return list(sorted(players.values(), key=_sort_key))
