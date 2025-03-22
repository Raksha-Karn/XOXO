import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Game, Move


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.user = self.scope['user']
        self.game_group_name = f'game_{self.game_id}'
        
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        game_state = self.get_game_state()
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'game_state': game_state
        }))
        
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
        
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', '')
        
        if message_type == 'make_move':
            row = data.get('row')
            col = data.get('col')
            
            valid, updated_state = self.make_move(row, col)
            if valid:
                event = {
                    'type': 'game_update',
                    'state': updated_state
                }
                await self.channel_layer.group_send(
                    self.game_group_name,
                    event
                )
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Invalid move!'
                }))
    
    async def game_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_update',
            'state': event['state']
        }))
        
    @database_sync_to_async
    def get_game_state(self):
        try:
            game = Game.objects.get(id=self.game_id)
            return {
                'board': game.board,
                'current_player': game.current_player,
                'status': game.status,
                'winner': game.winner,
                'player_x': game.player_x.username if game.player_x else None,
                'player_o': game.player_o.username if game.player_o else None,
            }
        except Game.DoesNotExist:
            return None
        
    @database_sync_to_async
    def make_move(self, row, col):
        try:
            game = Game.objects.get(id=self.game_id)
            if (game.current_player == 'X' and game.player_x != self.user) or (game.current_player == 'O' and game.player_o != self.user):
                return False, None
        
            if game.status != 'active':
                return False, None
            
            board = json.loads(game.board)
            if board[row][col] != '':
                return False, None
            
            board[row][col] = game.current_player
            
            winner = self.check_winner(board)
            is_draw = self.is_board_full(board)
            
            if winner:
                game.status = 'completed'
                game.winner = winner
            elif is_draw:
                game.status = 'draw'
            else:
                game.current_player = 'O' if game.current_player == 'X' else 'X'
            
            game.board = json.dumps(board)
            game.save()
            
            Move.objects.create(
                game=game,
                player=self.user,
                row=row,
                col=col,
                symbol=game.current_player
            )
            
            return True, self.get_game_state()
        except Game.DoesNotExist:
            return False, None
        
    def check_winner(self, board):
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] != '':
                return board[i][0]
            
            if board[0][i] == board[1][i] == board[2][i] != '':
                return board[0][i]
        
        if board[0][0] == board[1][1] == board[2][2] != '':
            return board[0][0]
        
        if board[0][2] == board[1][1] == board[2][0] != '':
            return board[0][2]
        
        return None

    def is_board_full(self, board):
        for row in board:
            if '' in row:
                return False
        return True