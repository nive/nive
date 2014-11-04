# Copyright 2012, 2013 Arndt Droullier, Nive GmbH. All rights reserved.
# Released under GPL3. See license.txt
#

__doc__ = """
Extension modules to store configuration values edited through the web interface.
Several backends are supported.

The functions only stores and loads the values passed to ``Save(values)``, not all configuration values.
Remaining values are loaded from python and configuration files in the file system.

For configuration storage and reference ``configuration.uid()`` is used as key.  
"""
import pickle
import json
import time
import logging 

from nive.definitions import implements, IPersistent, ModuleConf, Conf, IModuleConf
from nive.definitions import OperationalError, ProgrammingError





class PersistentConf(object):
    """
    configuration persistence base class ---------------------------------------
    """
    implements(IPersistent)
    
    def __init__(self, app, configuration):
        self.app = app
        self.conf = configuration
        
    def Load(self):
        """
        Load configuration values from backend and map to configuration.
        """
        raise TypeError, "subclass"
        
    def Save(self, values):
        """
        Store configuration values in backend.
        """
        raise TypeError, "subclass"
        
    def Changed(self):
        """
        Validate configuration and backend timestamp and check if 
        values have changed.
        """
        return False
        
    def _GetUid(self):
        return self.conf.uid()



        
def LoadStoredConfValues(app, pyramidConfig):
    # lookup persistent manager for configuration
    storage = app.Factory(IModuleConf, "persistence")
    if not storage:
        return
    try:
        db = app.NewDBApi()
        if not db:
            return
    except:
        return
    # adapters
    for conf in app.registry.registeredAdapters():
        storage(app=app, configuration=conf.factory).Load(db=db)
    for conf in app.registry.registeredUtilities():
        storage(app=app, configuration=conf.component).Load(db=db)
    db.close()
    

class DbPersistence(PersistentConf):
    """
    Stores configuration values in the configured databases' pool_sys table.
    """

    def Load(self, db=None):
        """
        Load configuration values from backend and map to configuration.
        Uses a raw database connection to access the database to allow being called 
        before startup. 
        """
        close = 0
        try:
            if not db:
                close = 1
                db = self.app.NewDBApi()
            sql = """select value,ts from pool_sys where id=%s""" % (self.app.NewConnection().placeholder)
            c=db.cursor()
            c.execute(sql, (self._GetUid(),))
            data = c.fetchall()
            c.close()
        except db.OperationalError:
            data = None
            db.rollback()
        except db.ProgrammingError:
            data = None
            db.rollback()
        except Exception, e:
            log = logging.getLogger(self.app.id)
            log.error("DbPersistence.Load() failed %s", str(e))
            return None
        if close:
            db.close()
        if data:
            try:
                values = json.loads(data[0][0])
            except ValueError:
                # Invalid data
                # bw 0.9.13 try previously used pickled data conversion
                try:
                    values = pickle.loads(data[0][0])
                except KeyError:
                    # Invalid data
                    return None
            lock = 0
            if self.conf.locked:
                lock = 1
                self.conf.unlock()
            self.conf.timestamp = data[0][1]
            #opt
            #for f in values.items():
            #    self.conf[f[0]] = f[1]
            self.conf.update(values)
            if lock:
                self.conf.lock()
            return values
        return None
        
    def Save(self, values, db=None):
        """
        Store configuration values in backend.
        Uses the datapool class to access the database.
        """
        ts = time.time()
        close = 0
        try:
            if not db:
                close = 1
                db = self.app.db
            sql = """select ts from pool_sys where id=%s""" % (db.placeholder)
            r = db.Query(sql, (self._GetUid(),))
            data = json.dumps(values)
            if len(r):
                db.UpdateFields("pool_sys", self._GetUid(), {"value":data,"ts":ts})
            else:
                db.InsertFields("pool_sys", {"value":data,"ts":ts, "id":self._GetUid()})
            db.Commit()
        except OperationalError: 
            data = None
            db.Undo()
        except ProgrammingError: 
            data = None
            db.Undo()
        if close:
            db.Close()
        lock = 0
        if self.conf.locked:
            lock = 1
            self.conf.unlock()
        self.conf.timestamp = ts
        #for f in values.items():
        #    self.conf[f[0]] = f[1]
        self.conf.update(values)
        if lock:
            self.conf.lock()
        return True
        
    def Changed(self):
        """
        Validate configuration timestamp and backend timestamp and check if 
        updates have occured.
        """
        return False


dbPersistenceConfiguration = ModuleConf(
    id = "persistence",
    name = u"Configuration persistence extension",
    context = DbPersistence,
    events = (Conf(event="finishRegistration", callback=LoadStoredConfValues),),
)

