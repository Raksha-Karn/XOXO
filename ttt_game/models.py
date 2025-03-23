from django.db import models
from django.contrib.auth.models import User
import json

# Create your models here.
class Game(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('draw', 'Draw'),
        ('waiting', 'Waiting for Player'),
    ]
    
    player_x = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='games_as_x')
    player_o = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='games_as_o')
    current_player = models.CharField(max_length=1,default='X')
    board = models.TextField(default=json.dumps([['','',''],['','',''],['','','']]))
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='waiting')
    winner = models.CharField(max_length=1,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'Game {self.id}: {self.player_x} vs {self.player_o}'
    
    def join_game(self,user):
        if self.status == 'waiting':
            if self.player_x is None:
                self.player_x = user
                self.save()
                return True
            elif self.player_o is None and self.player_x != user:
                self.player_o = user
                self.status = 'active'
                self.save()
                return True
            
        return False
    
    
class Move(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="moves")
    player = models.ForeignKey(User, related_name='moves', on_delete=models.CASCADE)
    row = models.IntegerField()
    col = models.IntegerField()
    symbol = models.CharField(max_length=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
