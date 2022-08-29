#!/usr/bin/env python3
#-*- coding: utf-8 -*-
 
# Very simple tetris implementation
#
# Control keys:
#       Down - Drop stone faster
# Left/Right - Move stone
#         Up - Rotate Stone clockwise
#     Escape - Quit game
#          P - Pause game
#     Return - Instant drop
#
# Have fun!
 
# NOTE: If you're looking for the old python2 version, see
#       <https://gist.github.com/silvasur/565419/45a3ded61b993d1dd195a8a8688e7dc196b08de8>
 
# Copyright (c) 2010 "Laria Carolin Chabowski"<me@laria.me>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
 
from random import randrange as rand
import pygame, sys, os, time

# EXE 파일생성시 리소프 파일의 임시경로를 반환
# 예) pyinstaller -w --add-data '.\pytetris\resource\*.*;resource' -F pytetris\pytetris.py
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path) 

# 사용되는 리소스 파일을 지정
# 아이콘 파일(png)
iconfile  = resource_path("pytetris/resource/icon.png") 

# 폰트 파일(ttf)
fontfile  = resource_path("pytetris/resource/consolaz.ttf") 

# 점수 파일(txt)
scorefile = resource_path("pytetris/resource/score.txt")

# 배경음악 파일(wav)
files_bgm =     [
                 "pytetris/resource/bgm01.wav"
                ,"pytetris/resource/bgm02.wav"
                ,"pytetris/resource/bgm03.wav"
                ,"pytetris/resource/bgm04.wav"
                ]

# 효과음 파일(wav)
files_sound =   [
                 "pytetris/resource/sound01.wav"    # 효과음 (한줄 격파)
                ,"pytetris/resource/sound02.wav"    # 효과음 (훅)
                ,"pytetris/resource/sound03.wav"    # 효과음 (게임종료)
                ]

# The configuration
font_size    = 16
font_color   = (255,255,255)    # 폰트색상
font_color_c = (255,255,  0)    # 폰트색상(치트 활성화 시)

cell_size  = 40
cols       = 10
rows       = 25
maxfps     = 30
 
colors = [
(0,   0,   0  ),
(255, 85,  85 ),
(100, 200, 115),
(120, 108, 245),
(255, 140, 50 ),
(50,  120, 52 ),
(146, 202, 73 ),
(150, 161, 218),
(35,  35,  35 ) # Helper color for background grid
]
 
# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],
 
    [[0, 2, 2],
     [2, 2, 0]],
 
    [[3, 3, 0],
     [0, 3, 3]],
 
    [[4, 0, 0],
     [4, 4, 4]],
 
    [[0, 0, 5],
     [5, 5, 5]],
 
    [[6, 6, 6, 6]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]

def rotate_clockwise(shape):
    return [[ shape[y][x] for y in range(len(shape)) ] for x in range(len(shape[0]) - 1, -1, -1)]
 
def check_collision(board, shape, offset):
    off_x, off_y = offset
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[ cy + off_y ][ cx + off_x ]:
                    return True
            except IndexError:
                return True
    return False
 
def remove_row(board, row):
    del board[row]
    return [[0 for i in range(cols)]] + board
 
def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy+off_y-1 ][cx+off_x] += val
    return mat1
 
def new_board():
    board = [[ 0 for x in range(cols) ] for y in range(rows)]
    board += [[ 1 for x in range(cols)]]
    return board
 
class TetrisApp(object):
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption("Py테트리스")
        pygame.display.set_icon(pygame.image.load(iconfile))
        pygame.key.set_repeat(250,25)

        self.width = cell_size*(cols+6)
        self.height = cell_size*rows
        self.rlim = cell_size*cols
        self.bground_grid = [[ 8 if x%2==y%2 else 0 for x in range(cols)] for y in range(rows)]
        #self.default_font = pygame.font.Font(pygame.font.get_default_font(), 14)
        self.default_font = pygame.font.Font(fontfile, font_size)
        self.screen = pygame.display.set_mode((self.width, self.height))

        pygame.event.set_blocked(pygame.MOUSEMOTION) # We do not need
                                                     # mouse movement
                                                     # events, so we
                                                     # block them.
        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        self.sound_mute = False     # 소리 끄기 여부
        self.cheat_use  = False     # cheat 사용 여부
        self.init_game()
 
    def new_stone(self):
        self.stone = self.next_stone[:]
        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(cols / 2 - len(self.stone[0])/2)
        self.stone_y = 0
 
        if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
            self.gameover = True
 
    def init_game(self):
        self.board = new_board()
        self.new_stone()
        self.level = 1
        self.score = 0
        self.scores = ""            # 게임 종료 점수
        self.lines = 0
        self.speed = 0              # 속도 초기화
        self.speed_max = False      # 최대속도여부
        self.sound_play_count = 0   # 효과음 재생 횟수
        #pygame.time.set_timer(pygame.USEREVENT+1, 1000)
        self.set_speed(0)

        self.play_bgm(files_bgm[0], -1)  # 배경음악을 재생한다.

    # 배경음악을 재생한다.
    def play_bgm(self, filename, playcount):
        if self.sound_mute == False:
            self.stop_bgm()
            pygame.mixer.music.load(resource_path(filename))
            pygame.mixer.music.play(playcount)  # playcount = -1 : 무한반복
            pass
    
    # 배경음악을 종료한다.
    def stop_bgm(self):
        #pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.stop()

    # 배경음악을 멈춘다, 다시 재생한다.
    def pause_bgm(self, flag):
        if self.sound_mute == False:
            if flag == True:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def set_mute(self):
        if self.sound_mute == False:
            self.sound_mute = True
            pygame.mixer.music.pause()
        else:
            self.sound_mute = False
            pygame.mixer.music.unpause()

    # 효과음을 재생한다.
    def play_sound(self, filename):
        if self.sound_mute == False:
            sound = pygame.mixer.Sound(resource_path(filename))
            sound.play()
 
    def disp_msg(self, msg, topleft):
        x,y = topleft
        for line in msg.splitlines():
            self.screen.blit(self.default_font.render(line, False, font_color if self.cheat_use == False else font_color_c, (0,0,0)), (x,y))
            y+=14
 
    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image =  self.default_font.render(line, False, font_color if self.cheat_use == False else font_color_c, (0,0,0))
 
            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y //= 2
            
            self.screen.blit(msg_image, (self.width // 2 - msgim_center_x, self.height // 2 - msgim_center_y + i * 22))
 
    def draw_matrix(self, matrix, offset):
        off_x, off_y  = offset
        for y, row in enumerate(matrix):
            for x, val in enumerate(row):
                if val:
                    #pygame.draw.rect(self.screen, colors[val], pygame.Rect((off_x+x) * cell_size, (off_y+y) * cell_size, cell_size, cell_size),0)
                    pygame.draw.rect(self.screen, colors[val], pygame.Rect((off_x+x) * cell_size+0.1, (off_y+y) * cell_size+0.1, cell_size-0.1, cell_size-0.1),0)    # 테투리 지정
 
    def add_cl_lines(self, n):
        linescores = [0, 40, 100, 300, 2400]
        self.lines += n
        self.score += linescores[n] * self.level
        if self.lines >= self.level*8:
            self.level += 1
            self.speed += 1
            
            self.set_speed(self.speed)  # 속도를 증가한다.
            '''
            if self.level == 6:
                self.play_bgm(files_bgm[1], -1)  # 배경음악을 재생한다.
            elif self.level == 11:
                self.play_bgm(files_bgm[2], -1)  # 배경음악을 재생한다.
            elif self.level == 16:
                self.play_bgm(files_bgm[3], -1)  # 배경음악을 재생한다.
            '''

    def set_speed(self, new_speed):
        self.speed = new_speed
        newdelay = 1000 - (50 * self.speed)   # 레벨당 속도가 50씩 증가
        newdelay = 100 if newdelay < 100 else newdelay
        # 최대속도 표시
        if newdelay == 100:
            self.speed_max = True
        else:
            self.speed_max = False
        pygame.time.set_timer(pygame.USEREVENT+1, newdelay)

        # 속도에 따라 배경음악을 제어한다.
        if self.speed == 0:
            self.play_bgm(files_bgm[0], -1)  # 배경음악을 재생한다.
        elif self.speed == 6:
            self.play_bgm(files_bgm[1], -1)  # 배경음악을 재생한다.
        elif self.speed == 11:
            self.play_bgm(files_bgm[2], -1)  # 배경음악을 재생한다.
        elif self.speed == 16:
            self.play_bgm(files_bgm[3], -1)  # 배경음악을 재생한다.

    def move(self, delta_x):
        if not self.gameover and not self.paused:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > cols - len(self.stone[0]):
                new_x = cols - len(self.stone[0])
            if not check_collision(self.board, self.stone, (new_x, self.stone_y)):
                self.stone_x = new_x
                
    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()
 
    def drop(self, manual):
        if not self.gameover and not self.paused:
            self.score += 1 if manual else 0
            self.stone_y += 1
            if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
                self.board = join_matrixes(self.board, self.stone, (self.stone_x, self.stone_y))
                self.new_stone()
                cleared_rows = 0
                while True:
                    for i, row in enumerate(self.board[:-1]):
                        if 0 not in row:
                            self.board = remove_row(self.board, i)
                            cleared_rows += 1
                            self.play_sound(files_sound[0])  # 효과음을 재생한다.
                            break
                    else:
                        break
                self.add_cl_lines(cleared_rows)
                return True
        return False
 
    def insta_drop(self):
        if not self.gameover and not self.paused:
            self.play_sound(files_sound[1]) # 효과음을 재생한다.
            while(not self.drop(True)):
                pass
 
    def rotate_stone(self):
        if not self.gameover and not self.paused:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(self.board, new_stone, (self.stone_x, self.stone_y)):
                #self.play_sound(files_sound[2]) # 효과음을 재생한다.
                self.stone = new_stone
 
    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_bgm(self.paused)  # 배경음악을 멈춘다, 다시 재생한다.
 
    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False
 
    # 치트를 활성화한다.
    def set_cheat_use(self):
        if self.cheat_use == False:
            self.cheat_use = True
            print("Cheat mode on !!!")
        else:
            self.cheat_use = False
            print("Cheat mode off !!!")
    
    # 치트1: 다음 블록으로 변경한다.
    def c_call_new_stone(self):
        if self.cheat_use == True:
            print("Get new stone !!")
            self.stone = self.next_stone[:]
            self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
            self.stone_x = int(cols / 2 - len(self.stone[0])/2)
            self.stone_y = 0
    
            if check_collision(self.board, self.stone, (self.stone_x, self.stone_y)):
                self.gameover = True

    # 치트2: 속도를 초기화한다.
    def c_init_speed(self):
        if self.cheat_use == True:
            print("Set init speed !!")
            self.speed = 0
            self.set_speed(0)
    
    #점수를 기록한다.
    def set_rec_score(self):
        with open(scorefile, "a", encoding="utf8") as f:
            f.write("{0:>10}".format(str(format(self.score, ','))) + " : " + time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time())) + "\n")
    
    # 점수 리스트를 반환한다.
    def get_score_list(self):
        rtn_list = ""
        with open(scorefile, "r", encoding="utf8") as f:
            score_list = f.readlines()
            score_list.sort()
            score_list.reverse()    # 내림차순 정렬 (반드시 그전에 오름차순 정렬을 해야 한다.)
            for i in range(0, 5):  # 상위 5개
                try:
                    rtn_list += str(i + 1) + ". " + score_list[i]
                except Exception as err:
                    break

        return rtn_list

    # 점수 및 랭킹 표시
    def disp_score_msg(self):
        new_score  = "{0:>10}".format(str(format(self.score, ','))) + " : " + time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time())) + "\n"
        if self.scores == "":    # 중복 기록 방지!!!
            self.scores = new_score
            with open(scorefile, "a", encoding="utf8") as f:
                f.write(new_score)

        disp_msg = "Game Over!\nYour score: %s\nPress space to continue\n\n\n%s" % (format(self.score, ','), self.get_score_list())
        #self.center_msg(disp_msg)
        for i, line in enumerate(disp_msg.splitlines()):
            msg_image =  self.default_font.render(line, False, font_color if self.cheat_use == False else font_color_c, (0,0,0))
 
            msgim_center_x, msgim_center_y = msg_image.get_size()
            msgim_center_x //= 2
            msgim_center_y = msgim_center_y / 2 + 100

            self.screen.blit(msg_image, (self.width // 2 - msgim_center_x, self.height // 2 - msgim_center_y + i * 22))
        
    def run(self):
        key_actions = {
            'ESCAPE': self.quit
           ,'LEFT'  : lambda:self.move(-1)
           ,'RIGHT' : lambda:self.move(+1)
           ,'DOWN'  : lambda:self.drop(True)
           ,'UP'    : self.rotate_stone
           ,'p'     : self.toggle_pause
           ,'SPACE' : self.start_game
           ,'RETURN': self.insta_drop
           ,'m'     : self.set_mute
           ,'c'     : self.set_cheat_use
           ,'n'     : self.c_call_new_stone     # cheat code1
           ,'0'     : self.c_init_speed         # cheat code2
        }
 
        self.gameover = False
        self.paused = False
 
        dont_burn_my_cpu = pygame.time.Clock()
        while 1:
            self.screen.fill((0,0,0))
            if self.gameover:
                self.stop_bgm()
                if self.sound_play_count < 2:
                    self.sound_play_count += 1
                if self.sound_play_count == 1:
                    self.play_sound(files_sound[2])

                self.disp_score_msg()
                #self.set_rec_score()
                #self.center_msg("Game Over!\nYour score: %s\nPress space to continue\n\n%s" % (format(self.score, ','), self.get_score_list()))
                
            else:
                if self.paused:
                    self.center_msg("Paused")
                else:
                    pygame.draw.line(self.screen, (255,255,255), (self.rlim+1, 0), (self.rlim+1, self.height-1))
                    self.disp_msg("Next:", (self.rlim+cell_size, cell_size))
                    self.disp_msg("Score: %s\n\nLines: %s\n\nLevel: %d\n\nSpeed: %s" % (format(self.score, ','), format(self.lines, ','), self.level, "MAX" if self.speed_max == True else self.speed), (self.rlim+cell_size, cell_size*5))
                    self.disp_msg(" Control keys:\n\n"\
                                 + " ↑     - Rotate Stone\n"\
                                 + " ↓     - Drop faster\n"\
                                 + " ← / → - Move stone\n"\
                                 + " P     - Pause game\n"\
                                 + " M     - Mute\n"\
                                 + " Return- Instant drop\n"\
                                 + " Esc   - Quit game", (self.rlim+(cell_size/3), cell_size*15))
                    self.draw_matrix(self.bground_grid, (0,0))
                    self.draw_matrix(self.board, (0,0))
                    self.draw_matrix(self.stone, (self.stone_x, self.stone_y))
                    self.draw_matrix(self.next_stone, (cols+1,2))
            pygame.display.update()
 
            for event in pygame.event.get():
                if event.type == pygame.USEREVENT+1:
                    self.drop(False)
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in key_actions:
                        if event.key == eval("pygame.K_" + key):
                            key_actions[key]()
 
            dont_burn_my_cpu.tick(maxfps)
 
if __name__ == '__main__':
    App = TetrisApp()
    App.run()
