# -*- coding: utf-8 -*-
from openfisca_core.simulations import Simulation
import openfisca_france

import sys


from openfisca_core.periods import period


from reforme import CPAMReform


class StripperReader(object):
    def __init__(self, reader):
        super(StripperReader, self).__init__()
        self.reader = reader

    def op(self, row):
        row = { fieldname.strip(): row[fieldname].strip() for fieldname in self.reader.fieldnames }
        return row

    def __iter__(self):
        self.reader.__iter__()
        return self

    def next(self):
        return self.op(self.reader.next())


def getPath(key, ext=''):
    return sys.argv[-1].format(key) + ext

situations = {
  'individus': {},
  'familles': {},
  'foyers_fiscaux': {},
  'menages': {},
}

ressourceMapping = {
    'MNTCHO_RES': 'chomage_net', # Allocations chômage
    'MNTPER_RES': 'pensions_alimentaires_percues', # Pensions alimentaires reçues
    'MNTRET_RES': 'retraite_nette', # Pensions, retraites et rentes
    'MNTPRE_RES': 'retraite_nette', # Préretraites
    'MNTSAL_RES': 'salaire_net', # Traitements et salaires

    'MNTAUT_RES': 'salaire_net', # Autre revenus : montants TODO LIBAUT_RES
    'MNTBOU_RES': 'salaire_net', # Bourses étude enseignement sup.
    'MNTCHA_RES': 'salaire_net', # Montant du chiffre d’affaire
    'MNTIJO_RES': 'salaire_net', # indemnités journalières
    'MNTNON_RES': 'salaire_net', # Revenus des professions non salariées
    'MNTPRF_RES': 'salaire_net', # prestations familiales
    'MNTSEC_RES': 'salaire_net', # Secours et aides réguliers
}

def main():
    periode = '2018-11'
    periode_1 = '2018-10'
    months = period('year:2018-11').offset(-1, 'year').get_subperiods('month')

    periodes = [periode]
    calculs = {
        #'acs_plafond': periodes,
        #'acs': periodes,
        'cmu_base_ressources': periodes,
        #'cmu_c': periodes,
    }

    import csv

    paths = [
        'cmu', 'coc', 'res'
    ]

    ids = []
    n_limit = 10e10

    import datetime
    now = datetime.datetime.now()
    timestamp = now.isoformat().replace(':','-').replace('.', '-')

    with open(getPath('cmu')) as csvfile:
        reader = StripperReader(csv.DictReader(csvfile, delimiter=';'))
        n = 0
        for row in reader:
            MATRICUL = row['ASSMAC_CMU'] + '_' + row['DATDEM_C']
            if len(ids) and MATRICUL not in ids:
                continue

            n = n + 1
            if n == n_limit:
                break
            situations['familles'][MATRICUL] = {
                'acs': {
                    periode_1: row['ACSM'] if row['C'] == 'B' else 0
                },
                'acs_plafond': {
                    periode_1: row['ACSPLA_CMU']
                },
                'af': { m: 0 for m in months },
                'aspa': { m: 0 for m in months },
                'cmu_c': {
                    periode_1: row['C'] == 'A'
                },
                'cmu_base_ressources': {
                    periode_1: row['TOTMNT_CMU'].replace(',', '.')
                },
                'rsa': {
                    periode: 0
                },
                'parents': [],
                'enfants': []
            }
            situations['foyers_fiscaux'][MATRICUL] = {
                'declarants': [],
                'personnes_a_charge': []
            }
            situations['menages'][MATRICUL] = {
                'personne_de_reference': [],
                'conjoint': [],
                'enfants': []
            }

    with open(getPath('coc')) as csvfile:
        reader = StripperReader(csv.DictReader(csvfile, delimiter=';'))
        n = 0
        for row in reader:
            GROUP = '_'.join([row['ASSMAC_COC'], row['DATDEM_C']])
            MATRICUL = '_'.join([GROUP, row['NAIDSI_COC'], row['B']])
            NAIDSI = row['NAIDSI_COC']
            if GROUP not in situations['familles']:
                continue

            situations['individus'][MATRICUL] = {
                'date_naissance': {
                    periode: '{0}-{1}-{2}'.format(NAIDSI[0:4], NAIDSI[4:6], NAIDSI[6:])
                }
            }

            if len(situations['familles'][GROUP]['parents']) == 0:
                situations['familles'][GROUP]['parents'].append(MATRICUL)
                situations['foyers_fiscaux'][GROUP]['declarants'].append(MATRICUL)
                situations['menages'][GROUP]['personne_de_reference'].append(MATRICUL)
            elif len(situations['familles'][GROUP]['parents']) == 1:
                situations['familles'][GROUP]['parents'].append(MATRICUL)
                situations['foyers_fiscaux'][GROUP]['declarants'].append(MATRICUL)
                situations['menages'][GROUP]['conjoint'].append(MATRICUL)
            else:
                situations['familles'][GROUP]['enfants'].append(MATRICUL)
                situations['foyers_fiscaux'][GROUP]['personnes_a_charge'].append(MATRICUL)
                situations['menages'][GROUP]['enfants'].append(MATRICUL)

            n = n + 1
    print(n)

    with open(getPath('res')) as csvfile:
        reader = StripperReader(csv.DictReader(csvfile, delimiter=';'))
        n = 0
        for row in reader:
            GROUP = '_'.join([row['ASSMAC_RES'], row['DATDEM_R']])
            MATRICUL = '_'.join([GROUP, row['NAIDSI_RES'], row['B']])
            if MATRICUL not in situations['individus']:
                continue

            individu = situations['individus'][MATRICUL]
            for inputName, outputName in ressourceMapping.iteritems():
                individu[outputName] = {
                    month: 0 for month in months
                }

            for inputName, outputName in ressourceMapping.iteritems():
                for month in months:
                    individu[outputName][month] += float(row[inputName].replace(',', '.')) / 12

            famille = situations['familles'][GROUP]
            famille['aide_logement'] = {
                month: float(row['MNTAPL_RES'].replace(',', '.')) / 12 for month in months
            }
            famille['aide_logement'][periode] = float(row['MNTAPL_RES'].replace(',', '.')) / 12
            famille['cmu_forfait_logement_al'] = { periode: float(row['MNTAPL_RES'].replace(',', '.')) }

            n = n + 1
        print(n)

    from pprint import pprint
    #pprint(situations)

    tax_benefit_system = CPAMReform(openfisca_france.CountryTaxBenefitSystem())
    simulation_actuelle = Simulation(
        tax_benefit_system=tax_benefit_system,
        simulation_json=situations,
        trace=True)

    import numpy

    import pandas as pd

    threshold = 10
    results = pd.DataFrame()
    results['ids'] = simulation_actuelle.get_variable_entity('af').ids

    for calcul, periodes in calculs.iteritems():
        print(calcul)
        ids = simulation_actuelle.get_variable_entity(calcul).ids
        for periode in periodes:
            valeurs = simulation_actuelle.calculate(calcul, periode)
            sources = simulation_actuelle.calculate(calcul, periode_1)

            print (numpy.histogram(valeurs - sources))
            print(100.0 * sum((valeurs != 0) * (abs(valeurs - sources) < threshold)) / sum(valeurs != 0))

            results[calcul + periode_1] = sources
            results[calcul + periode] = valeurs
            results[calcul + 'adiff'] = abs(sources - valeurs)

            results = results.sort_values(by=[calcul + 'adiff'], ascending=False)

    if len(ids) == 1:
        simulation_actuelle.tracer.print_computation_log()

    outpath = getPath(key='', ext=timestamp + '.out.csv')
    print(outpath)
    results.to_csv(outpath, index=False, decimal=",", sep=";")


if __name__ == '__main__':
    sys.exit(main())
