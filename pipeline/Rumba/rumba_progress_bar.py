from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtUiTools import *
from PySide2.QtGui import *
import os
from os.path import join
from os import getcwd
from sys import argv, exit
from Common import disrupt_stylesheet

class RumbaProgressWindow(QObject):

    def __init__(self):
        super().__init__()
        
        ui_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), r'UI\rumba_loading.ui')
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(ui_file)
        ui_file.close()
        q_pixmap = QPixmap(join(getcwd(), r'UI\rumba_cat_icon.png'))
        q_icon = QIcon(q_pixmap)
        self.ui.setWindowIcon(q_icon)
        self.ui.move(450,200)
        self.skip_factor = 25
        self.bar_1_counter = 0
        self.bar_2_counter = 0

        movie_file = join(getcwd(), r'UI\rumba_cat_128.gif')
        self.movie = QMovie(movie_file, QByteArray(), self)
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.ui.movie_screen.setMovie(self.movie)
        self.movie.start()

    def update_bar_1(self):
        self.ui.bar_1.setValue(self.ui.bar_1.value() + 1)
        if self.bar_1_counter % self.skip_factor == 0:
            QCoreApplication.processEvents()
        self.bar_1_counter += 1

    def update_bar_2(self):
        self.ui.bar_2.setValue(self.ui.bar_2.value() + 1)
        if self.bar_2_counter % self.skip_factor == 0:
            QCoreApplication.processEvents()
        self.bar_2_counter += 1

if __name__ == '__main__':
    app = QApplication(argv)
    disrupt_stylesheet.set_stylesheet(app)
    rumba_progress_window = RumbaProgressWindow()
    rumba_progress_window.ui.show()
    exit(app.exec_())
