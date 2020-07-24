# Manage a list of available vdjbase-style databases

from os.path import join, isdir
from os import listdir
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import app
import os.path

VDJBASE_DB_PATH = os.path.join(app.config['STATIC_PATH'], 'study_data/VDJbase/db')

Session = sessionmaker()

class ContentProvider():
    db = None
    connection = None
    session = None

    def __init__(self, path):
        self.db = create_engine('sqlite:///' + path + '?check_same_thread=false', echo=False, pool_threadlocal=True)
        self.connection = self.db.connect()
        self.session = Session(bind=self.connection)


def vdjbase_db_init():
    vdjbase_dbs = {}

    for species in listdir(VDJBASE_DB_PATH):
        p = join(VDJBASE_DB_PATH, species)
        if isdir(p) and species[0] != '.':
            for name in listdir(p):
                if isdir(join(p, name)) and name[0] != '.':
                    if species not in vdjbase_dbs:
                        vdjbase_dbs[species] = {}
                    vdjbase_dbs[species][name] = ContentProvider(join(p, name, 'db.sqlite3'))
                    if species == 'Human':
                        update_gene_order(vdjbase_dbs[species][name].session)
    return vdjbase_dbs

IGH_LOCUS_ORDER = [
    "IGHV7-81", "IGHV5-78", "IGHV3-74", "IGHV3-73", "IGHV3-72", "IGHV3-71", "IGHV2-70", "IGHV1-69D", "IGHV1-f",
    "IGHV2-70D", "IGHV1-69", "IGHV1-68", "IGHV1-69-2", "IGHV3-69-1",
    "IGHV3-66", "IGHV3-64", "IGHV3-63", "IGHV3-62", "IGHV4-61", "IGHV4-59", "IGHV1-58", "IGHV4-55", "IGHV3-54",
    "IGHV3-53", "IGHV3-52",
    "IGHV5-51", "IGHV3-49", "IGHV3-48", "IGHV3-47", "IGHV1-46", "IGHV1-45", "IGHV3-43", "IGHV3-43D", "IGHV7-40",
    "IGHV4-39", "IGHV1-38-4", "IGHV3-38-3", "IGHV4-38-2",
    "IGHV3-38", "IGHV3-35", "IGHV7-34-1", "IGHV4-34", "IGHV3-33-2", "IGHV3-33", "IGHV3-32",
    "IGHV4-31", "IGHV3-30-52", "IGHV3-30-5", "IGHV3-30-42", "IGHV4-30-4", "IGHV3-30-33", "IGHV3-30-3",
    "IGHV3-30-22", "IGHV4-30-2", "IGHV4-30-1", "IGHV3-30-2", "IGHV3-30", "IGHV3-29", "IGHV4-28",
    "IGHV2-26", "IGHV3-25", "IGHV1-24", "IGHV3-23", "IGHV3-23D", "IGHV3-22", "IGHV3-21", "IGHV3-20", "IGHV3-19",
    "IGHV1-18", "IGHV3-16",
    "IGHV3-15", "IGHV3-13", "IGHV3-11", "IGHV2-10", "IGHV3-9", "IGHV5-10-1", "IGHV1-8", "IGHV3-64D", "IGHV3-7",
    "IGHV2-5", "IGHV7-4-1", "IGHV4-4", "IGHV1-3", "IGHV1-2", "IGHV6-1",
    "IGHV2-10", "IGHV3-52", "IGHV3-47", "IGHV3-71", "IGHV3-22", "IGHV4-55", "IGHV1-68",
    "IGHV5-78", "IGHV3-32", "IGHV3-33-2", "IGHV3-38-3", "IGHV3-25", "IGHV3-19", "IGHV7-40", "IGHV3-63",
    "IGHV3-62", "IGHV3-29", "IGHV3-54", "IGHV1-38-4", "IGHV7-34-1", "IGHV1-38-4", "IGHV3-30-2",
    "IGHV3-69-1", "IGHV3-30-22", "IGHV1-f", "IGHV3-30-33", "IGHV3-38", "IGHV7-81", "IGHV3-35",
    "IGHV3-16", "IGHV3-30-52", "IGHV1-69D", "IGHD1-14", "IGHV3-30-42",
    "IGHD1-1", "IGHD2-2", "IGHD3-3", "IGHD6-6", "IGHD1-7", "IGHD2-8",
    "IGHD3-9", "IGHD3-10", "IGHD4-11", "IGHD5-12", "IGHD6-13", "IGHD1-14",
    "IGHD2-15", "IGHD3-16",
    "IGHD4-17", "IGHD5-18", "IGHD6-19", "IGHD1-20", "IGHD2-21", "IGHD3-22",
    "IGHD4-23", "IGHD5-24", "IGHD6-25", "IGHD1-26", "IGHD7-27",
    "IGHJ1", "IGHJ2", "IGHJ3", "IGHJ4", "IGHJ5", "IGHJ6"
]

PSEUDO_GENES = [
    "IGHV2-10", "IGHV3-52", "IGHV3-47", "IGHV3-71", "IGHV3-22", "IGHV4-55", "IGHV1-68",
                    "IGHV5-78", "IGHV3-32", "IGHV3-33-2", "IGHV3-38-3", "IGHV3-25", "IGHV3-19", "IGHV7-40", "IGHV3-63",
                    "IGHV3-62", "IGHV3-29", "IGHV3-54", "IGHV1-38-4", "IGHV7-34-1", "IGHV1-38-4", "IGHV3-30-2",
                    "IGHV3-69-1", "IGHV3-30-22", "IGHV1-f", "IGHV3-30-33", "IGHV3-38", "IGHV7-81", "IGHV3-35",
                    "IGHV3-16","IGHV3-30-52","IGHV1-69D", "IGHD1-14", "IGHV3-30-42"
]

# Hack to provide sort orders and pseudogene indicators for heavy chain until we get them from the pipeline

from db.vdjbase_model import Gene

def update_gene_order(session):
    test = session.query(Gene.alpha_order).filter(Gene.name == 'IGHJ6').one_or_none()

    if test is None or test[0] is None:
        genes = session.query(Gene).all()

        extra = 1
        alpha = 1
        for gene in genes:
            if gene.name in IGH_LOCUS_ORDER:
                gene.locus_order = IGH_LOCUS_ORDER.index(gene.name)
            else:
                gene.locus_order = len(IGH_LOCUS_ORDER) + extra
                extra = extra + 1
            gene.pseudo_gene = 1 if gene.name in PSEUDO_GENES else 0
            gene.alpha_order = alpha
            alpha += 1

        session.commit()
