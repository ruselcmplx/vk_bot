import random
import re


HANGMANPICS = ['''
  +------+
  |&#8195;&#8195;|
  |
  |
  |
  |
=========''', '''
  +------+
  |&#8195;&#8195;|
  |&#12288;&#12288;O
  |
  |
  |
=========''', '''
  +------+
  |&#8195;&#8195;|
  |&#12288;&#12288;O
  |&#12288;&#12288;|
  |
  |
=========''', '''
  +------+
  |&#8195;&#8195;|
  |&#12288;&#12288;O
  |&#12288;&#12288;/|
  |
  |
=========''', '''
  +------+
  |&#8195;&#8195;|
  |&#12288;&#12288;O
  |&#12288;&#12288;/|\\
  |    
  |
=========''', '''
  +------+
  |&#8195;&#8195;|
  |&#12288;&#12288;O
  |&#12288;&#12288;/|\\
  |&#12288;&#12288;/
  |
=========''', '''
  +------+
  |&#8195;&#8195;|
  |&#12288;&#12288;O
  |&#12288;&#12288;/|\\
  |&#12288;&#12288;/ \\
  |
=========''']


class HANGMAN():
    def __init__(self, player_id, game_start):
        self.player_id = player_id
        self.mistakes = 0
        self.win = False
        self.hangman_pic = HANGMANPICS[0]
        self.used_letters = []
        self.game_start = game_start
        with open('./mnt/nouns.txt', encoding='utf8') as f:
            word = random.choice(f.readlines()).strip()
            self.word = word
            shown_word = [word[0]]
            shown_word.extend(['_']*(len(word)-2))
            shown_word.append(word[-1])
            self.shown_word = shown_word

    def guess(self, letter):
        res_text = ''
        if (letter not in self.used_letters):
            self.used_letters.append(letter)
        if letter in self.word[1:-1]:
            shown_word = self.shown_word
            pattern = r'{}'.format(letter)
            matches = re.finditer(pattern, self.word)
            for i in [match.start(0) for match in matches]:
                shown_word[i] = self.word[i]
            if '_' not in self.shown_word:
                self.win = True
                res_text = 'Ты победил!\nСлово {}'.format(self.word)
            else:
                res_text = ' '.join(shown_word)
        else:
            if self.mistakes < 5:
                self.mistakes += 1
                self.hangman_pic = HANGMANPICS[self.mistakes]
                res_text = self.hangman_pic + '\nНет совпадений, использованные буквы: {}\n'.format(
                    ', '.join(self.used_letters))+' '.join(self.shown_word)
            else:
                self.hangman_pic = HANGMANPICS[self.mistakes+1]
                res_text = self.hangman_pic + \
                    '\nТы проиграл\nСлово {}'.format(self.word)
                return [False, res_text]

        return [not self.win, res_text]


if __name__ == "__main__":
    game = HANGMAN(1)
    input_phrase = 'Cлово: '+' '.join(game.shown_word)
    while (not game.win) and game.mistakes < 6:
        guess_letter = input(input_phrase + '\n').strip()
        if guess_letter and len(guess_letter) == 1:
            res = game.guess(guess_letter)
            if(res):
                input_phrase = res
            else:
                input_phrase = game.hangman_pic + '\nНет совпадений'
        else:
            input_phrase = 'Введите букву'

    input('You win\n' if game.win else game.hangman_pic + '\nYou lost\n')
