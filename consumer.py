import logging
import multiprocessing
import sys
from hashlib import sha1
from os import kill, makedirs, listdir
from os.path import join, isdir
from shutil import move
from signal import SIGTERM
from time import sleep
from traceback import print_exc

# Make a log file
rootLogger = logging.basicConfig(filename='client.log',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rootLogger = logging.getLogger('forwarder_client')

# Make a streamhandler to log to console too
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
consoleHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(consoleHandler)


def run_command_local(file):
    """
    Takes in a file name and does something with it.
    MUST be static to work with apply_async nicely
    :param file: Path to file
    :return: None
    """
    out_dir = 'done'
    if not isdir(out_dir):
        makedirs(out_dir)
    try:
        m = sha1()
        try:
            with open(file, 'rb') as f:
                for chunk in f.read(1024*1024):
                    if chunk:
                        m.update(chunk)
                    else:
                        break
        except:
            print print_exc()
        expected_hash = m.hexdigest()
        rootLogger.info( expected_hash)
        move(file, out_dir)


    except:
        rootLogger.error(print_exc())

class Consumer(multiprocessing.Process):
    def __init__(self, job_queue):
        multiprocessing.Process.__init__(self)
        self.job_queue = job_queue
        self.workers = multiprocessing.cpu_count() -1

    def run(self):
        pool = multiprocessing.Pool(processes=int(self.workers))
        proc_name = self.name
        while True:
            try:
                next_task = self.job_queue.get()
                if next_task is None:
                    rootLogger.error( '%s: Exiting' % proc_name)
                    break
                rootLogger.info('%s: %s' % (proc_name, next_task))
                pool.apply_async(run_command_local, (next_task,))
            except KeyboardInterrupt:
                pool.join()
                pool.close()
                break
        return

class Client():
    def __init__(self, job_queue):
        self.job_queue = job_queue
        self.listen_directory = 'listen'
        self.temp_directory = 'temp'
        self.beacon = 10
        self.logger = rootLogger

    def do_listen(self):
        if not isdir(self.listen_directory):
            makedirs(self.listen_directory)
        if not isdir(self.temp_directory):
            makedirs(self.temp_directory)
        files = listdir(self.listen_directory)

        for f in files:
            move(join(self.listen_directory,f), self.temp_directory)
            self.job_queue.put(join(self.temp_directory, f))


    def run(self):
        while True:
            try:
                self.do_listen()
                sleep(float(self.beacon))
            except KeyboardInterrupt:
                break
            except:
                rootLogger.error('Unexpected error. Exiting...')
                rootLogger.error(print_exc())
                self.job_queue.put(None)
                break


def main():
    # Create a queue for jobs
    job_queue = multiprocessing.Queue()

    pids = []
    try:
        c = Consumer(job_queue)
        c.start()
        pids.append(c.pid)

        client = Client(job_queue)
        client.run()
    except KeyboardInterrupt:
        rootLogger.error('Main keyboard error handling')
        for p in pids:
            kill(p, SIGTERM)
        #sys.exit(0)
    except:
        rootLogger.error('Unexpected error.')
        rootLogger.error(print_exc())
        #sys.exit(0)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()