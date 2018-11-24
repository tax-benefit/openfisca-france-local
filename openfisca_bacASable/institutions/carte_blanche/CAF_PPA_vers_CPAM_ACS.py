# -*- coding: utf-8 -*-
from openfisca_core.simulations import Simulation
import openfisca_france

import os
import numpy
import sys

periode = '2018-11'
periodes = [periode]
calculs = {
    'ppa': periodes,
    'acs': periodes,
    'cmu_c': periodes,
}

m3 = '2018-10'
m2 = '2018-09'
m1 = '2018-08'
m0 = '2018-07'

from openfisca_core.periods import period


ninePreviousMonths = [period('month:2018-07').offset(-i, 'month') for i in range(0,9)]

n_limit = 20000
def generate_CAF(path):
    import csv

    situations = {
      'individus': {},
      'familles': {},
      'foyers_fiscaux': {},
      'menages': {},
    }

    with open(path) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        n = 0
        for row in reader:
            if n == n_limit:
                return situations
            MATRICUL = row['rownum']
            situations['individus'][MATRICUL] = {
                'salaire_net': {
                    m : 0 for m in ninePreviousMonths #(float(row['MTOTFOY1']) + float(row['MTOTFOY2']) + float(row['MTOTFOY3']))
                }
            }

            situations['individus'][MATRICUL]['salaire_net'][periode] = row['MTOTFOY1']
            situations['individus'][MATRICUL]['salaire_net'][m1] = row['MTOTFOY1']
            situations['individus'][MATRICUL]['salaire_net'][m2] = row['MTOTFOY2']
            situations['individus'][MATRICUL]['salaire_net'][m3] = row['MTOTFOY3']

            situations['familles'][MATRICUL] = {
                'acs': {
                    m3: 0
                },
                'cmu_c': {
#                    periode: False,
#                    m3: False
                },
                'parents': [MATRICUL],
                'ppa': {
                    m3: row['MTPPAVER']
                },
                'rsa_nb_enfants': {
                    m3: row['PANBENAU'],
                }
            }
            situations['foyers_fiscaux'][MATRICUL] = {
                'declarants': [MATRICUL]
            }
            situations['menages'][MATRICUL] = {
                'personne_de_reference': [MATRICUL]
            }
            n = n + 1

    return situations


def main():
    inputpath = sys.argv[-1]
    filepath = os.path.splitext(inputpath)[0]
    situation =  generate_CAF(inputpath)

    tax_benefit_system = openfisca_france.CountryTaxBenefitSystem()
    simulation_actuelle = Simulation(
        tax_benefit_system=tax_benefit_system,
        simulation_json=situation)

    import pandas as pd
    csv_input = pd.read_csv(inputpath, sep=";", nrows=n_limit)

    for calcul, periodes in calculs.iteritems():
        print(calcul)
        ids = simulation_actuelle.get_variable_entity(calcul).ids
        for periode in periodes:
            valeurs = simulation_actuelle.calculate(calcul, periode)
            sources = simulation_actuelle.calculate(calcul, m3)

            csv_input['_'.join(['openfisca', calcul, periode])] = valeurs
            #print (numpy.histogram(valeurs - sources))

            resultat = dict(zip(ids, zip(valeurs, sources)))
            for matricul, valeurs in resultat.iteritems():
                calculee, reelle = valeurs

    csv_input.to_csv(filepath + '.out.csv', index=False, decimal=",", sep=";")

if __name__ == '__main__':
    sys.exit(main())
