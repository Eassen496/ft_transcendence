from typing import Any
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from ..models import Game, Score

class GamesHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self: APIView, request: Any) -> Response:  # noqa: ANN401
        finished_games = Game.objects.filter(Q(status='finished') | Q(status='saving'), tournament_name__isnull=True).order_by('-created_at')
        games_history = []
        for i, game in enumerate(finished_games, start=0):
            if i == 15:
                break
            scores = Score.objects.filter(games=game)
            game_json = {}
            for j, score in enumerate(scores, start=1):
                game_json['player%d' % j] = score.player.username
                game_json['display%d' % j]= score.player.display_name
                game_json['score%d' % j] = score.score
            game_json['blockchain_hash'] = game.blockchain_hash
            games_history.append(game_json)
        return Response(games_history, status=status.HTTP_200_OK)

class GamesHistoryForUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self: APIView, request: Any, username: str) -> Response: # noqa: ANN401
        finished_games = Game.objects.filter(Q(status='finished') | Q(status='saving')).order_by('-created_at')
        games_history = []
        i = 0
        for game in finished_games:
            if i == 5:
                break
            if not game.scores.filter(player__username=username).exists():
                continue
            scores = Score.objects.filter(games=game)
            game_json = {}
            for j, score in enumerate(scores, start=1):
                game_json['player%d' % j] = score.player.username
                game_json['display%d' % j]= score.player.display_name
                game_json['score%d' % j] = score.score
                game_json['winner'] = game.winner.username
            game_json['blockchain_hash'] = game.blockchain_hash
            i += 1
            games_history.append(game_json)
        return Response(games_history, status=status.HTTP_200_OK)
