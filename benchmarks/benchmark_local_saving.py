import json
import pickle
import _pickle as cPickle
import sqlite3
import tables
import numpy

def benchmark_text_record_metric(self, model, version, experiment, run_id, name, value):
    """
    This function serves to benchmark the time is takes to save files to disk, using file saving
    """
    file = open('benchmark_text.txt','w')
    file.write('Hello World') 
    file.close()

def benchmark_JSON_record_metric(self, model, version, experiment, run_id, name, value):   
    """
    This function serves to benchmark the time is takes to save files to disk, using JSON
    """
    data = [model, version, experiment, run_id, name, value]
    with open('benchmark_JSON.json', 'w') as outfile:
        json.dump(data, outfile)

def benchmark_pickle_record_metric(self, model, version, experiment, run_id, name, value):
    """
    This function serves to benchmark the time is takes to save files to disk, using pickle
    """
    metric = ['test value', 'test value2', 'test value3']
    file_name = 'benchmark_pickle'
    with open(file_name, 'wb') as fileObject:
        pickle.dump(metric, fileObject)

def benchmark_cpickle_record_metric(self, model, version, experiment, run_id, name, value):
    """
    This function serves to benchmark the time is takes to save files to disk, using file cPickle
    """
    metric = ['test value', 'test value2', 'test value3']
    file_name = 'benchmark_cPickle'
    with open(file_name,  'wb') as fileObject:
        cPickle.dump(metric, fileObject)

def benchmark_sqlite_record_metric(self, model, version, experiment, run_id, name, value):
    """
    This function serves to benchmark the time is takes to save files to disk, using sqlite3
    """
    metric = [model, version, experiment, run_id, name, value]
    conn = sqlite3.connect('benchmark_sqlite.db')
    c = conn.cursor()
    # insert a row of data
    c.execute('INSERT INTO metrics VALUES (?,?,?,?,?,?)', metric)
    # save the changes
    conn.commit()
    # close the connection
    conn.close()

def benchmark_pytables_record_metric(self, model, version, experiment, run_id, name, value):
    """
    This function serves to benchmark the time is takes to save files to disk, using pytables
    """
    h5file = tables.open_file('benchmark_pytables.h5', mode='w', title='Test File')
    group = h5file.create_group('/',  'Metric', 'Metric Information')
    table = h5file.create_table(group, 'readout', Metric, 'readout example')
    metric = table.row
    metric['model'] = model
    metric['version'] = version
    metric['experimentl'] = experiment
    metric['run_id'] = run_id
    metric['name'] = name
    metric['value'] = value

    # Insert a new metric record
    metric.append()
    table.flush()


class Metric(tables.IsDescription):
    model 		= tables.StringCol()
    version	 	= tables.Int32Col()
    experiment	        = tables.StringCol()
    run_id		= tables.StringCol()
    timestamp	        = tables.StringCol()
    metric 		= tables.StringCol()
    value		= tables.Float32Col()
    