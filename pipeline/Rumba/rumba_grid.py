import itertools

class WorldGrid(object):
    WORLD_OFFSET_X = 4096
    WORLD_OFFSET_Y = 3072
    CELL_SIZE = 128
    CELL_COUNT_X = int(WORLD_OFFSET_X*2 / CELL_SIZE)
    CELL_COUNT_Y = int(WORLD_OFFSET_Y*2 / CELL_SIZE)
    CELL_GEOMETRY = [(0, 0), (0, 128), (128, 128), (128, 0)]

    def __init__(self):
        super(WorldGrid, self).__init__()
        self.cells = dict()
        self.build_grid()

    def build_grid(self):

        rgb_values = list(itertools.product(range(256), repeat=3))
        step = int(16777215 / WorldGrid.CELL_COUNT_X ** 2)
        counter = 0
        x_range = range(WorldGrid.CELL_COUNT_X)
        y_range = range(WorldGrid.CELL_COUNT_Y)
        x_min, x_max = x_range[0], x_range[-1]
        x_sum = x_min + x_max
        for x in x_range:
            for y in y_range:
                reversed_x = x_sum - x
                cell = WorldCell()
                cell.coord = (reversed_x, y)
                cell.selection_color = rgb_values[counter]
                cell.generation_position = (x * WorldGrid.CELL_SIZE, y * WorldGrid.CELL_SIZE)
                world_x = (cell.coord[0] * WorldGrid.CELL_SIZE) - WorldGrid.WORLD_OFFSET_X
                world_y = (cell.coord[1] * WorldGrid.CELL_SIZE) - WorldGrid.WORLD_OFFSET_Y
                cell.world_position = (world_x, world_y)
                cell.points = cell.generate_world_position_geometry()
                self.cells[cell.coord] = cell
                counter += step

class WorldCell(object):
    def __init__(self):
        super(WorldCell, self).__init__()
        self.coord = None
        self.cell = None
        self.selection_color = None
        self.filter_result = dict()
        self.stat_color = (0,0,0,0)
        self.stat_resources = None
        self.stat_instances = None
        self.generation_position = None
        self.points = None
        self.world_instances = set()

    def generate_world_position_geometry(self):
        world_cell_geometry = []
        for position in WorldGrid.CELL_GEOMETRY:
            x = position[0] + self.generation_position[0]
            y = position[1] + self.generation_position[1]
            world_cell_geometry.append((x, y))

        return world_cell_geometry