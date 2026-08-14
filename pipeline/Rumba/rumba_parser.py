from Common.file_helpers import get_files
import Rumba.rumba_data_classes
from rumba_database import SQLiteDB
from os.path import getmtime
import time
import pickle
from sqlite3 import Binary
from multiprocessing import Pool


def get_rumba_data_classes():
    classes_set = set()
    for object_name in dir(Rumba.rumba_data_classes):
        obj = eval("Rumba.rumba_data_classes." + object_name)
        if type(obj) is not type:
            continue
        if not hasattr(obj, 'TYPE'):
            continue
        if hasattr(obj, 'IS_LIBRARY_OBJECT'):
            continue
        if obj.TYPE == 'DObject':
            continue

        # if obj.TYPE != 'Material': # TEST! Should be commented at all times.
        #     print(obj.TYPE)
        #     continue

        classes_set.add(obj)
    return classes_set


def parse_data(data_class, files, progress_window=None):
    profiling_time = 0.0

    db = SQLiteDB(data_class.TYPE, data_class.VERSION)
    conn = db.connect_to_db()
    cursor = conn.cursor()
    db.create_tables(cursor)
    timestamps = db.get_timestamps(cursor)
    files_to_insert = set()
    files_to_delete = set()

    if progress_window is not None:
        progress_window.ui.bar_2.reset()
        progress_window.ui.bar_2.setMaximum(len(files)-1)

    for file in files:

        if progress_window is not None:
            # progress_window.ui.label_2.setText(file)
            progress_window.update_bar_2()

        local_start_time = time.time()
        status = db.check_timestamp(file, timestamps)
        profiling_time += (time.time() - local_start_time)
        if status:
            continue

        if status is not None:
            files_to_delete.add((file,))
        
        d_object = data_class(file)

        binary_d_object = Binary(pickle.dumps(d_object, pickle.HIGHEST_PROTOCOL))
        files_to_insert.add((file, getmtime(file), binary_d_object, d_object.TYPE))

    if files_to_delete:
        db.delete_files(cursor, files_to_delete)
        print(len(files_to_delete), data_class.TYPE, 'files deleted')
    if files_to_insert:
        db.insert_files(cursor, files_to_insert)
        print(len(files_to_insert), data_class.TYPE, 'files inserted')

    db.disconnect_from_db(conn)

def parse_all(rumba_data_classes, progress_window=None):
    #rumba_data_classes = [Rumba.rumba_data_classes.DMaterial,Rumba.rumba_data_classes.DGeometry]
    d_objects = dict()
    ##TIME##########################################
    start = time.time()
    print ('started in:', start)
    ###################  MULTI THREADING ###############
    if progress_window is not None:
        progress_window.ui.label_1.setText("Generating data on multiple threads (Thanks Chris). UI might stop responding, don't worry")
    pool = Pool(11)
    pool.map(parse_multithreaded, rumba_data_classes)
    pool.close()
    ##END TIME ###############
    elapsed = time.time() - start
    print('\n Multithreading done in:', elapsed, '\n')

    ###################  LINEAR ########################
    for rumba_data_class in rumba_data_classes:
        if progress_window is not None:
            progress_window.ui.label_1.setText('Getting ' + rumba_data_class.TYPE + ' files from database.')
            progress_window.update_bar_1()
        db = SQLiteDB(rumba_data_class.TYPE, rumba_data_class.VERSION)
        conn = db.connect_to_db()
        cursor = conn.cursor()
        d_objects[rumba_data_class.TYPE] = db.get_objects_from_db(cursor, rumba_data_class.TYPE, progress_window)
        db.disconnect_from_db(conn)

    ##END TIME ###############
    elapsed = time.time() - start
    print('done in:', elapsed)
    ##END TIME ###############
    return d_objects


def parse_multithreaded(rumba_data_class):
    files = set()    
    for extension in rumba_data_class.EXTENSIONS:
        files = files.union(get_files(rumba_data_class.PATH_TO_FILES, extension))
    parse_data(rumba_data_class, files)


if __name__ == "__main__":
    start_time = time.time()
    parse_all()
    print("--- %s seconds ---" % (time.time() - start_time))
