import pygame
import random
import numpy as np
import math

size = (1200, 800)
spacing = 40

# Set up stuff for pygame display.
pygame.init()
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Polynomial Grapher")
done = False
clock = pygame.time.Clock()
font = pygame.font.Font("Arial.ttf", 18)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)


# Make the dashes for the graph.
def draw_graph():
    x_center = round(size[0] / 2)
    y_center = round(size[1] / 2)

    pygame.draw.line(screen, BLACK, [x_center, 0], [x_center, size[1]], 2)
    pygame.draw.line(screen, BLACK, [0, y_center], [size[0], y_center], 2)

    for x in range(0, x_center + 1, spacing):
        pygame.draw.line(screen, BLACK, [x_center + x, y_center - 5], [x_center + x, y_center + 5], 1)
        pygame.draw.line(screen, BLACK, [x_center - x, y_center - 5], [x_center - x, y_center + 5], 1)

    for y in range(0, y_center + 1, spacing):
        pygame.draw.line(screen, BLACK, [x_center - 5, y_center + y], [x_center + 5, y_center + y], 1)
        pygame.draw.line(screen, BLACK, [x_center - 5, y_center - y], [x_center + 5, y_center - y], 1)


# Convert readable coordinates (2, 5) to position on screen (680, 200) or do the inverse.
# int_lock makes the coordinates round to the nearest 1.
def human_to_computer_coords(x, y, inverse=False, int_lock=True):
    x_center = round(size[0] / 2)
    y_center = round(size[1] / 2)

    if inverse:
        x = (x - x_center) / spacing
        y = -(y - y_center) / spacing
    else:
        x = x * spacing + x_center
        y = -y * spacing + y_center

    if int_lock:
        x = round(x)
        y = round(y)

    return x, y


# Graph lines between each point in X and Y.
def graph_lines(x, y, color):
    x_list = x
    y_list = y

    for i in range(len(x_list)):
        x_list[i], y_list[i] = human_to_computer_coords(x_list[i], y_list[i])

    coords = [(x_list[i], y_list[i]) for i in range(len(x_list))]
    pygame.draw.aalines(screen, color, False, coords)


# Create a readable format using the coefficients (x^2-3x+2).
def create_readable_function(coeffs):
    output = 'f(x) = '
    j = 0
    for i, coeff in enumerate(coeffs):
        if -0.0001 < coeff < 0.0001:
            continue
        j += 1
        sign = ''
        if coeff >= 0 and not j == 1:
            sign = '+'

        power = (len(coeffs)-1)-i
        if power == 0:
            power = ''
        elif power == 1:
            power = 'x'
        else:
            power = 'x^' + str(power)

        coeff = round(coeff, 4)
        if coeff == 1 and not i == len(coeffs)-1:
            coeff = ''
        elif coeff == -1 and not i == len(coeffs)-1:
            coeff = '-'
        else:
            coeff = '{:g}'.format(coeff)

        output += '{}{}{}'.format(sign, coeff, power)

    if output == 'f(x) = ':
        output = 'f(x) = 0'

    return output


def get_coefficients(points):
    x = np.array([i[0] for i in points], dtype=float)
    y = np.array([i[1] for i in points], dtype=float)

    return np.polyfit(x, y, len(x)-1)


def create_function_points(coeffs, x_min, x_max, segments):
    x = np.linspace(x_min, x_max, segments)
    y = np.polyval(coeffs, x)

    return x, y


# Object that can be dragged and drawn on the screen.
class Point:
    def __init__(self, x, y):
        self._coords = [x, y]

        self.int_lock = False
        self.dragging = False

        self.human_x, self.human_y = human_to_computer_coords(self.coords[0], self.coords[1], inverse=True)
        self._coords[0], self._coords[1] = human_to_computer_coords(self.human_x, self.human_y)

        # Create an area of pixels that show when the point was clicked on.
        self.grab_area = []
        for i in range(-10, 11):
            for j in range(-10, 11):
                self.grab_area.append((self._coords[0] + i, self._coords[1] + j))

    # Check if the point has been clicked on.
    def is_clicked(self, coords):
        if coords in self.grab_area:
            self.dragging = True
            return True

    def update_position(self, zoom=False):
        if not zoom:
            self.human_x, self.human_y = human_to_computer_coords(self._coords[0], self._coords[1], inverse=True,
                                                                  int_lock=self.int_lock)

        self._coords[0], self._coords[1] = human_to_computer_coords(self.human_x, self.human_y)

        self.grab_area = []
        for i in range(-7, 8):
            for j in range(-7, 8):
                self.grab_area.append((self._coords[0] + i, self._coords[1] + j))

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, value):
        self._coords = value

        self.update_position()

    def draw(self):
        pygame.draw.circle(screen, BLUE, [self._coords[0], self._coords[1]], 6)


def derivative(coeffs, x_min, x_max):
    x = np.linspace(x_min, x_max, int(size[0]))
    y = []
    d = 0.00000001
    for i in x:
        y.append((np.polyval(coeffs, (i + d)) - np.polyval(coeffs, i))/d)
    return x, y


# Create initial point at (0, 0).
points = [Point(*human_to_computer_coords(0, 0))]

global_int_lock = False
derivative_toggle = False
coeffs = []

while not done:
    # Event handler.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for point in points:
                    if point.is_clicked(pygame.mouse.get_pos()):
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                for point in points:
                    point.dragging = False

        elif event.type == pygame.KEYDOWN:
            # Add a random point somewhere on the screen.
            if event.key == pygame.K_UP:
                points.append(Point(random.randint(0, size[0]), random.randint(0, size[1])))
                points[-1].int_lock = global_int_lock

            elif event.key == pygame.K_DOWN:
                if len(points) > 1:
                    points.pop()

            # Toggle int_lock, if switching on all points will move to the nearest integer.
            elif event.key == pygame.K_l:
                global_int_lock = not global_int_lock

                for point in points:
                    point.int_lock = global_int_lock
                    point.update_position()

            # Zoom in by changing the pixel spacing between numbers.
            elif event.key == pygame.K_RIGHT:
                if spacing < 320:
                    spacing = int(spacing * 2)
                    for point in points:
                        point.update_position(zoom=True)

            # Zoom out by changing the pixel spacing between numbers.
            elif event.key == pygame.K_LEFT:
                if spacing > 10:
                    spacing = int(spacing * 0.5)
                    for point in points:
                        point.update_position(zoom=True)

            elif event.key == pygame.K_p:
                print(create_readable_function(coeffs), coeffs)

            elif event.key == pygame.K_d:
                derivative_toggle = not derivative_toggle

    # Update each points position if dragging, add each points coordinates to point_coords.
    current_points = []
    for point in points:
        if point.dragging:
            point.coords = list(pygame.mouse.get_pos())
        current_points.append((point.human_x, point.human_y))

    # Check if there are no duplicate x values.
    x_list = [point[0] for point in current_points]
    if len(x_list) == len(set(x_list)):
        # Get the coefficients for each point in point_coords.
        coeffs = get_coefficients(current_points)

        function_text = font.render(create_readable_function(coeffs), True, BLACK)

        # Create the x and y values for each point of the function.
        x_max = int((size[0] / 2) / spacing) + 1
        X, Y = create_function_points(coeffs, -x_max, x_max, int(size[0]))

    else:
        function_text = font.render('f(x) = undefined', True, BLACK)
        X, Y = [0, 0], [0, 0]

    # Clear screen
    screen.fill(WHITE)

    # Drawing code
    draw_graph()

    x_max = int((size[0] / 2) / spacing) + 1
    graph_lines(X, Y, BLACK)

    if derivative_toggle:
        graph_lines(*derivative(coeffs, -x_max, x_max), RED)

    screen.blit(function_text, (10, 10))

    for point in points:
        point.draw()

    # Update screen
    pygame.display.flip()

    # Limit FPS
    clock.tick(60)

pygame.quit()
