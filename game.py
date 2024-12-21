import arcade
import json

# Константы экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Pong Game"
BEST_TIME_FILE = "best_time.txt"
PLAYER_DATA_FILE = "players.json"
KEYBOARD_LAYOUT = [
    "QWERTYUIOP",
    "ASDFGHJKL",
    "ZXCVBNM"
]


class Button:
    def __init__(self, x, y, width, height, text):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self):
        arcade.draw_rectangle_filled(self.x, self.y, self.width, self.height, arcade.color.LIGHT_GRAY)
        arcade.draw_rectangle_outline(self.x, self.y, self.width, self.height, arcade.color.BLACK, 2)
        arcade.draw_text(self.text, self.x, self.y, arcade.color.BLACK, 18, anchor_x="center", anchor_y="center")

    def is_clicked(self, x, y):
        return self.x - self.width / 2 < x < self.x + self.width / 2 and self.y - self.height / 2 < y < self.y + self.height / 2


class Ball(arcade.Sprite):
    def __init__(self, speed_multiplier=1.0):
        super().__init__()
        self.texture = arcade.make_circle_texture(20, arcade.color.RED)
        self.change_x = 5 * speed_multiplier
        self.change_y = -5 * speed_multiplier

    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y

        if self.left <= 0 or self.right >= SCREEN_WIDTH:
            self.change_x *= -1

        if self.top >= SCREEN_HEIGHT:
            self.change_y *= -1


class Bar(arcade.Sprite):
    def __init__(self, width, height):
        super().__init__()
        self.width = width
        self.height = height
        self.change_x = 0
        self.texture = arcade.Texture.create_filled(
            name="bar_texture", size=(width, height), color=arcade.color.BLUE
        )

    def update(self):
        self.center_x += self.change_x
        if self.left < 0:
            self.left = 0
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH


class Game(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        self.player_name = ""
        self.player_list = []
        self.keyboard = []
        self.space_button = None
        self.backspace_button = None
        self.done_button = None

        self.bar = None
        self.ball = None
        self.time_elapsed = 0
        self.best_time = 0
        self.best_player = "None"
        self.state = "select_name"
        self.countdown = 3.0
        self.game_over = False

        self.load_best_time()
        self.load_player_data()
        self.create_keyboard()

    def create_keyboard(self):
        self.keyboard = []
        start_y = SCREEN_HEIGHT / 2 - 50
        key_spacing = 50
        for row_index, row in enumerate(KEYBOARD_LAYOUT):
            start_x = SCREEN_WIDTH / 2 - len(row) * key_spacing / 2 + key_spacing / 2
            for col_index, letter in enumerate(row):
                x = start_x + col_index * key_spacing
                y = start_y - row_index * key_spacing
                self.keyboard.append(Button(x, y, 40, 40, letter))

        self.space_button = Button(SCREEN_WIDTH / 2, start_y - len(KEYBOARD_LAYOUT) * key_spacing - 20, 200, 40, "SPACE")
        self.backspace_button = Button(SCREEN_WIDTH / 2, start_y - len(KEYBOARD_LAYOUT) * key_spacing - 70, 200, 40, "BACKSPACE")
        self.done_button = Button(SCREEN_WIDTH / 2 + 200, SCREEN_HEIGHT / 2 + 50, 100, 40, "Done")

    def load_best_time(self):
        try:
            with open(BEST_TIME_FILE, "r") as file:
                data = file.read().split(" by ")
                self.best_time = float(data[0])
                self.best_player = data[1]
        except (FileNotFoundError, ValueError, IndexError):
            self.best_time = 0
            self.best_player = "None"

    def save_best_time(self):
        with open(BEST_TIME_FILE, "w") as file:
            file.write(f"{self.best_time:.2f} by {self.best_player}")

    def load_player_data(self):
        try:
            with open(PLAYER_DATA_FILE, "r") as file:
                self.player_list = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.player_list = []

    def save_player_data(self):
        with open(PLAYER_DATA_FILE, "w") as file:
            json.dump(self.player_list[:5], file)  # Ограничиваем список до 5 имен

    def setup_game(self):
        print(f"setup_game called, resetting game_over: {self.game_over}")
        self.bar = Bar(width=80, height=20)
        self.bar.center_x = SCREEN_WIDTH / 2
        self.bar.center_y = SCREEN_HEIGHT / 5
        self.ball = Ball(speed_multiplier=1.0)
        self.ball.center_x = SCREEN_WIDTH / 2
        self.ball.center_y = SCREEN_HEIGHT / 2
        self.time_elapsed = 0
        self.countdown = 3.0
        self.state = "countdown"
        self.game_over = False  # Сбрасываем состояние завершения игры

    def on_draw(self):
        self.clear((255, 255, 255))
        if self.state == "select_name":
            self.draw_select_name()
        elif self.state == "enter_name":
            self.draw_name_input()
        elif self.state == "countdown":
            arcade.draw_text(
                f"{int(self.countdown) + 1}",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                arcade.color.BLACK, 60,
                anchor_x="center"
            )
        elif self.state == "game" and not self.game_over:  # Добавлено условие проверки game_over
            self.bar.draw()
            self.ball.draw()
            # Отображение текущего времени и лучшего результата
            arcade.draw_text(f"Time: {self.time_elapsed:.2f}", 10, SCREEN_HEIGHT - 30, arcade.color.BLACK, 16)
            arcade.draw_text(f"Best: {self.best_time:.2f} by {self.best_player}", 10, SCREEN_HEIGHT - 60,
                             arcade.color.BLACK, 16)
        elif self.game_over:  # Отдельное условие для завершения игры
            print("Drawing Game Over Screen")  # Отладочный вывод
            arcade.draw_text(
                "GAME OVER!",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40,
                arcade.color.RED_DEVIL, 50,
                anchor_x="center", bold=True
            )
            arcade.draw_text(
                "Press ENTER to Restart",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 10,
                arcade.color.ORANGE, 24,
                anchor_x="center"
            )
            arcade.draw_text(
                f"Your Time: {self.time_elapsed:.2f}",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60,
                arcade.color.BLACK, 18,
                anchor_x="center"
            )
            arcade.draw_text(
                f"Best: {self.best_time:.2f} by {self.best_player}",
                SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100,
                arcade.color.BLACK, 18,
                anchor_x="center"
            )

    def draw_select_name(self):
        arcade.draw_text("Select Your Name:", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150, arcade.color.BLACK, 24, anchor_x="center")
        start_y = SCREEN_HEIGHT / 2 + 100
        for index, name in enumerate(self.player_list):
            y = start_y - index * 50
            Button(SCREEN_WIDTH / 2 - 100, y, 200, 40, name).draw()
            Button(SCREEN_WIDTH / 2 + 150, y, 40, 40, "X").draw()
        Button(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100, 200, 40, "New Name").draw()

    def draw_name_input(self):
        arcade.draw_text("Enter Your Name:", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100, arcade.color.BLACK, 24, anchor_x="center")
        arcade.draw_text(self.player_name, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, arcade.color.BLACK, 24, anchor_x="center")
        for button in self.keyboard:
            button.draw()
        self.space_button.draw()
        self.backspace_button.draw()
        self.done_button.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.state == "select_name":
            for index, name in enumerate(self.player_list):
                if Button(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2 + 100 - index * 50, 200, 40, name).is_clicked(x, y):
                    self.player_name = name
                    self.setup_game()
                    return
                if Button(SCREEN_WIDTH / 2 + 150, SCREEN_HEIGHT / 2 + 100 - index * 50, 40, 40, "X").is_clicked(x, y):
                    del self.player_list[index]
                    self.save_player_data()
                    return
            if Button(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100, 200, 40, "New Name").is_clicked(x, y):
                self.state = "enter_name"

        elif self.state == "enter_name":
            for key in self.keyboard:
                if key.is_clicked(x, y) and len(self.player_name) < 15:
                    self.player_name += key.text
            if self.space_button.is_clicked(x, y):
                self.player_name += " "
            if self.backspace_button.is_clicked(x, y):
                self.player_name = self.player_name[:-1]
            if self.done_button.is_clicked(x, y) and self.player_name:
                if self.player_name not in self.player_list:
                    self.player_list.insert(0, self.player_name)
                    self.save_player_data()
                self.setup_game()

    def on_update(self, delta_time):
        if self.state == "countdown":
            # Уменьшаем отсчёт времени перед началом игры
            self.countdown -= delta_time
            if self.countdown <= 0:
                self.state = "game"
        elif self.state == "game" and not self.game_over:
            # Обновляем таймер, только если игра активна
            self.time_elapsed += delta_time
            self.ball.update()
            self.bar.update()
            # Проверка столкновения мяча с ракеткой
            if self.ball.bottom <= self.bar.top and self.bar.left <= self.ball.center_x <= self.bar.right:
                self.ball.change_y *= -1
            # Проверяем, упал ли мяч ниже экрана
            if self.ball.top < 0:
                if self.time_elapsed > self.best_time:
                    self.best_time = self.time_elapsed
                    self.best_player = self.player_name
                    self.save_best_time()
                self.game_over = True

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.bar.change_x = -7
        elif key == arcade.key.RIGHT:
            self.bar.change_x = 7
        elif key == arcade.key.ENTER and self.game_over:
            self.setup_game()

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.bar.change_x = 0


if __name__ == "__main__":
    window = Game(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    arcade.run()

