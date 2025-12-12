import pygame
import random
import sys
import json
import os

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1200, 700
FPS = 60
BG_COLOR = (35, 24, 40)

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cozy Autumn Cafe")
CLOCK = pygame.time.Clock()

TITLE_FONT = pygame.font.SysFont("arial", 40, bold=True)
HEADER_FONT = pygame.font.SysFont("arial", 26, bold=True)
NORMAL_FONT = pygame.font.SysFont("arial", 20)
SMALL_FONT = pygame.font.SysFont("arial", 16)

BROWN_LIGHT = (210, 180, 140)
BROWN_DARK = (120, 80, 40)
BROWN_MEDIUM = (160, 100, 50)
GOLD = (255, 215, 0)
TEXT_COLOR = (255, 230, 200)
WHITE = (255, 255, 255)
GREEN = (100, 150, 80)
HOVER_COLOR = (240, 200, 160)

class Upgrade:
    def __init__(self, name, x, y, cost, profit_boost, tip_boost=0, emoji=""):
        self.name = name
        self.emoji = emoji
        self.rect = pygame.Rect(x, y, 220, 55)
        self.base_cost = cost
        self.cost = cost
        self.profit_boost = profit_boost
        self.tip_boost = tip_boost
        self.level = 0
        self.hover = False

    def update(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def draw(self, surface, total_money):
        color = HOVER_COLOR if self.hover else BROWN_LIGHT
        affordable = total_money >= self.cost
        if not affordable:
            color = tuple(int(c * 0.5) for c in color)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, BROWN_DARK, self.rect, 2, border_radius=10)
        name_text = SMALL_FONT.render(f"{self.emoji} {self.name} L{self.level}", True, BROWN_DARK)
        surface.blit(name_text, (self.rect.x + 10, self.rect.y + 8))
        cost_text = SMALL_FONT.render(f"¥{self.cost}", True, BROWN_DARK)
        surface.blit(cost_text, (self.rect.x + 10, self.rect.y + 30))

    def can_purchase(self, total_money):
        return total_money >= self.cost

    def purchase(self):
        self.level += 1
        self.cost = int(self.base_cost * (1.2 ** self.level))
        return self.profit_boost, self.tip_boost

class Tip:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.vy = random.uniform(-3, -1)
        self.radius = 18
        self.lifetime = 0
        self.max_lifetime = 400
        self.angle = random.uniform(0, 360)

    def update(self):
        self.vy += 0.2
        self.y += self.vy
        self.lifetime += 1
        self.angle += 5

    def draw(self, surface):
        alpha = int(255 * max(0, 1 - self.lifetime / self.max_lifetime))
        coin_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(coin_surface, (*GOLD, alpha), (self.radius, self.radius), self.radius)
        pygame.draw.circle(coin_surface, (*BROWN_DARK, alpha), (self.radius, self.radius), self.radius, 3)
        surface.blit(coin_surface, (int(self.x - self.radius), int(self.y - self.radius)))
        value_text = SMALL_FONT.render(str(self.value), True, BROWN_DARK)
        surface.blit(value_text, (int(self.x - value_text.get_width() / 2), int(self.y - 10)))

    def is_clicked(self, mouse_x, mouse_y):
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        return (dx * dx + dy * dy) <= (self.radius ** 2)

    def is_dead(self):
        return self.lifetime >= self.max_lifetime or self.y > HEIGHT + 100

class CafeGame:
    def __init__(self):
        self.total_money = 500
        self.profit_per_second = 2
        self.tips_per_second = 0.5
        self.tips = []
        self.cafe_level = 0
        self.money_earned_total = 500
        self.total_tips_clicked = 0
        self.upgrades = [
            Upgrade("Better Beans", 20, 100, 50, 1, 0, "☕"),
            Upgrade("Warm Lights", 20, 165, 100, 2, 0.5, "💡"),
            Upgrade("Soft Music", 20, 230, 300, 5, 1, "🎵"),
            Upgrade("Cat Barista", 20, 295, 1000, 15, 2, "🐱"),
            Upgrade("Decorations", 20, 360, 5000, 40, 3, "🌸"),
            Upgrade("Big Expansion", 20, 425, 15000, 100, 5, "🏢"),
        ]
        self.money_tick = 0
        self.tip_spawn_tick = 0
        self.load_game()

    def save_game(self):
        data = {
            "total_money": self.total_money,
            "profit_per_second": self.profit_per_second,
            "tips_per_second": self.tips_per_second,
            "cafe_level": self.cafe_level,
            "upgrades": [{"level": u.level, "cost": u.cost} for u in self.upgrades]
        }
        try:
            with open("cafe_save.json", "w") as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def load_game(self):
        if os.path.exists("cafe_save.json"):
            try:
                with open("cafe_save.json", "r") as f:
                    data = json.load(f)
                self.total_money = max(0, data.get("total_money", 500))
                self.profit_per_second = data.get("profit_per_second", 2)
                self.tips_per_second = data.get("tips_per_second", 0.5)
                self.cafe_level = data.get("cafe_level", 0)
                upgrades_data = data.get("upgrades", [])
                for i, u_data in enumerate(upgrades_data):
                    if i < len(self.upgrades):
                        self.upgrades[i].level = u_data.get("level", 0)
                        self.upgrades[i].cost = u_data.get("cost", self.upgrades[i].base_cost)
            except:
                pass

    def handle_input(self, mouse_pos, mouse_clicked):
        if mouse_clicked:
            mx, my = mouse_pos
            for upgrade in self.upgrades:
                if upgrade.rect.collidepoint(mx, my):
                    if upgrade.can_purchase(self.total_money):
                        self.total_money -= upgrade.cost
                        profit_gain, tip_gain = upgrade.purchase()
                        self.profit_per_second += profit_gain
                        self.tips_per_second += tip_gain
                        self.cafe_level += 1
            for tip in self.tips[:]:
                if tip.is_clicked(mx, my):
                    self.total_money += tip.value
                    self.total_tips_clicked += 1
                    self.tips.remove(tip)

    def update(self):
        self.money_tick += 1
        if self.money_tick >= FPS:
            self.total_money += self.profit_per_second
            self.money_tick = 0
        self.tip_spawn_tick += 1
        tip_spawn_rate = max(10, FPS / (self.tips_per_second + 0.1))
        if self.tip_spawn_tick >= tip_spawn_rate and random.random() < 0.7:
            self.spawn_tip()
            self.tip_spawn_tick = 0
        for tip in self.tips[:]:
            tip.update()
            if tip.is_dead():
                self.tips.remove(tip)

    def spawn_tip(self):
        x = random.randint(500, WIDTH - 100)
        y = random.randint(150, 250)
        value = random.randint(10, 100)
        self.tips.append(Tip(x, y, value))

    def draw(self):
        WIN.fill(BG_COLOR)
        self.draw_background()
        self.draw_cafe()
        self.draw_left_panel()
        for tip in self.tips:
            tip.draw(WIN)
        title = TITLE_FONT.render("Cozy Autumn Cafe", True, TEXT_COLOR)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 15))
        pygame.display.update()

    def draw_background(self):
        leaves = [(80, 100), (150, 150), (200, 120), (1050, 120), (1100, 160), (1000, 140)]
        for x, y in leaves:
            pygame.draw.polygon(WIN, (200, 60, 40), [(x, y), (x + 25, y + 20), (x + 20, y + 40), (x - 5, y + 30)])

    def draw_cafe(self):
        cafe_x, cafe_y = 480, 150
        cafe_width, cafe_height = 450, 400
        pygame.draw.rect(WIN, BROWN_MEDIUM, (cafe_x, cafe_y, cafe_width, cafe_height), border_radius=20)
        pygame.draw.rect(WIN, BROWN_DARK, (cafe_x, cafe_y, cafe_width, cafe_height), 4, border_radius=20)
        roof_points = [(cafe_x, cafe_y), (cafe_x + cafe_width, cafe_y), (cafe_x + cafe_width - 40, cafe_y - 60), (cafe_x + 40, cafe_y - 60)]
        pygame.draw.polygon(WIN, (140, 50, 30), roof_points)
        pygame.draw.polygon(WIN, BROWN_DARK, roof_points, 3)
        pygame.draw.rect(WIN, (160, 100, 50), (cafe_x + 40, cafe_y + 200, cafe_width - 80, 100), border_radius=8)
        pygame.draw.rect(WIN, (80, 80, 80), (cafe_x + 100, cafe_y + 100, 50, 70))
        pygame.draw.circle(WIN, (150, 150, 150), (cafe_x + 125, cafe_y + 90), 15)
        pygame.draw.rect(WIN, (200, 150, 100), (cafe_x + 200, cafe_y + 160, 40, 50), border_radius=3)
        level_text = NORMAL_FONT.render(f"Level: {self.cafe_level}", True, TEXT_COLOR)
        WIN.blit(level_text, (cafe_x + 130, cafe_y + 300))

    def draw_left_panel(self):
        pygame.draw.rect(WIN, (60, 40, 50), (0, 50, 380, HEIGHT - 50))
        pygame.draw.line(WIN, BROWN_DARK, (380, 50), (380, HEIGHT), 3)
        panel_title = HEADER_FONT.render("Upgrades", True, TEXT_COLOR)
        WIN.blit(panel_title, (20, 60))
        for upgrade in self.upgrades:
            upgrade.update(pygame.mouse.get_pos())
            upgrade.draw(WIN, self.total_money)
        money_text = HEADER_FONT.render(f"¥{int(self.total_money)}", True, GOLD)
        WIN.blit(money_text, (20, HEIGHT - 100))
        profit_text = NORMAL_FONT.render(f"Profit/sec: ¥{self.profit_per_second}", True, TEXT_COLOR)
        WIN.blit(profit_text, (20, HEIGHT - 60))
        tips_text = NORMAL_FONT.render(f"Tips/sec: {self.tips_per_second:.1f}", True, TEXT_COLOR)
        WIN.blit(tips_text, (20, HEIGHT - 25))

def main():
    game = CafeGame()
    running = True
    while running:
        CLOCK.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.save_game()
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.handle_input(pygame.mouse.get_pos(), True)
        game.update()
        game.draw()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
