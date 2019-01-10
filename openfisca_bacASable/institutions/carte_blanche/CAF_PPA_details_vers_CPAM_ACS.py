# -*- coding: utf-8 -*-
from openfisca_core.simulations import Simulation
import openfisca_france

import csv
import datetime
import numpy
import pandas as pd
from pprint import pprint
import re
import sys

from openfisca_core.periods import period

# find *.csv -type f -exec iconv -f iso-8859-1 -t utf-8 "{}" -o "{}"utf8.csv \;

def getPath(key, ext=''):
    return sys.argv[1].format(key) + ext

def getMonth(string):
    return re.sub('^(?P<jour>\d{2})/(?P<mois>\d{2})/(?P<annee>\d{4})$', '\g<annee>-\g<mois>', string)

situations = {
  'individus': {},
  'familles': {},
  'foyers_fiscaux': {},
  'menages': {},
}

def main():
    if len(sys.argv) < 2:
        raise ValueError('Un chemin de la forme \'/chemin/vers/dossier/{0}.csv\' doit être passé en paramètre.')
    variable = 'ppa_versee'
    tax_benefit_system = openfisca_france.CountryTaxBenefitSystem()

    periode = '2018-11'
    ref_periode = '2017-11'
    months = period('year:' + periode).offset(-1, 'year').get_subperiods('month')

    periodes = [periode]
    calculs = {
        variable: periodes,
    }


    excludedIds = []
    if len(sys.argv)>2:
        excludedIds = sys.argv[2].split(',')
        print(str(len(excludedIds)) + ' excluded Ids')

    limitedIds = []
    n_limit = 10e4

    now = datetime.datetime.now()
    timestamp = now.isoformat().replace(':','-').replace('.', '-')

    with open(getPath('DRT')) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        n = 0
        for row in reader:
            MATRICUL = row['MATRICUL']

            if MATRICUL in excludedIds and MATRICUL not in limitedIds:
                continue

            if len(limitedIds) and MATRICUL not in limitedIds:
                continue

            if row['NATPF'] != 'PPA' or row['MOISDROV'] != '01/11/2018':
                continue

            if row['MTDROVAL'] == '0.00':
                pass#continue

            n = n + 1
            if n > n_limit:
                break

            situations['familles'][MATRICUL] = {
                'parents': [],
                'enfants': [],
                variable: {
                    ref_periode: row['MTDROVAL']
                },
                'rsa_nb_enfants': {},
                'af': {},
                'af_base': {},
                'ppa_forfait_logement': {},
                'rsa_isolement_recent': {}
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
    print(n)

    with open(getPath('PAD')) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        n = 0
        for row in reader:
            MATRICUL = row['MATRICUL']

            if MATRICUL not in situations['menages']:
                continue
            n = n + 1

            demandeur = row['NUIDEMPA']

            situations['familles'][MATRICUL]['ppa_mois_demande']= {
                'ETERNITY': getMonth(row['DTPMTRIR']) + '-01'
            }

            situations['individus'][demandeur] = {
#                'taux_incapacite': { m: 0.9 for m in months },
#                'aah': { m: 532.2 for m in months },
            }
            situations['familles'][MATRICUL]['parents'].append(demandeur)
            situations['foyers_fiscaux'][MATRICUL]['declarants'].append(demandeur)
            situations['menages'][MATRICUL]['personne_de_reference'].append(demandeur)
    print(n)

    with open(getPath('PAG')) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        n = 0
        for row in reader:
            MATRICUL = row['MATRICUL']

            if MATRICUL not in situations['menages']:
                continue
            n = n + 1

            mois = getMonth(row['MOIPRFIC'])

            situations['familles'][MATRICUL]['af'][mois] = row['MTPFPAF']
            situations['familles'][MATRICUL]['af_base'][mois] = row['MTPFPAF']
            situations['familles'][MATRICUL]['rsa_nb_enfants'][mois] = row['NBENFPPA']
            situations['familles'][MATRICUL]['ppa_forfait_logement'][mois] = row['MTFLOPAF']
            situations['familles'][MATRICUL]['rsa_isolement_recent'][periode] = False#row['SIFAMPAF'] == 'Isolé' and int(row['NBENFPPA'])>0
    print(n)

    ressourceMapping = {
        'Allocations de chômage': 'chomage_net',
        'Argent placé': None,
        'Autres IJSS (maladie, AT, MP)': 'indemnites_journalieres_maladie',
        'Autres revenus imposables': None,
        'Indemnités maternité _ paternité _ adoption': 'indemnites_journalieres_maternite',
        'Pension d\'invalidité': 'pensions_invalidite',
        'Pension de vieillesse imposable': 'retraite_nette',
        'Pensions alimentaires reçues': 'pensions_alimentaires_percues',
        'Remunération stage formation': 'revenus_stage_formation_pro',
        'Rente AT à titre personnel': None,
        'Ressources nulles': None,
        'Revenu des professions non salariés CGA ou trimestriel': None,
        'Revenu ETI/marin pêcheur/exploitant agricole': 'tns_benefice_exploitant_agricole',
        'Revenus d\'activité salariée': 'salaire_net',
        'Revenus d\' activité évalués professions non salariées. Spécifique PPA': 'salaire_net',
        'Revenus du patrimoine. Spécifique PPA': 'revenus_locatifs',
    }

    with open(getPath('RSM')) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        n = 0
        for row in reader:
            MATRICUL = row['MATRICUL']

            if MATRICUL not in situations['menages']:
                continue

            ressource = ressourceMapping[row['NATRESS']]

            if row['TITRESMO'] != 'Ressources mensuelles RSA ou PPA':
                if row['TITRESMO'] == 'Ressources mensuelles AAH' and ressource == 'salaire_net':
                    ressource = 'salaire_imposable'
                else:
                    continue

            individu = row['NUINPERS']

            if individu not in situations['individus']:
                if row['TYPEPER'] == 'Enfant':
                    situations['individus'][individu] = {}
                    situations['familles'][MATRICUL]['enfants'].append(individu)
                    situations['foyers_fiscaux'][MATRICUL]['personnes_a_charge'].append(individu)
                    situations['menages'][MATRICUL]['enfants'].append(individu)
                else:
                    situations['individus'][individu] = {}
                    situations['familles'][MATRICUL]['parents'].append(individu)
                    situations['foyers_fiscaux'][MATRICUL]['personnes_a_charge'].append(individu)
                    situations['menages'][MATRICUL]['conjoint'].append(individu)

            mois = getMonth(row['MOISRESS'])
            montant = float(row['MTNRESSM'].replace(',', '.'))

            if ressource in ['tns_benefice_exploitant_agricole']:
                montant = montant * 12
                mois = '2017'

            if not ressource:
                continue

            n = n + 1
            if ressource not in situations['individus'][individu]:
                situations['individus'][individu][ressource] = {
                    mois: 0
                }

            if mois not in situations['individus'][individu][ressource]:
                situations['individus'][individu][ressource][mois] = 0

            situations['individus'][individu][ressource][mois] += montant
    print(n)

    simulation_actuelle = Simulation(
        tax_benefit_system=tax_benefit_system,
        simulation_json=situations,
        trace=True)

    threshold = 10
    results = pd.DataFrame()
    results['ids'] = simulation_actuelle.get_variable_entity('af').ids

    for calcul, periodes in calculs.iteritems():
        print(calcul)
        ids = simulation_actuelle.get_variable_entity(calcul).ids
        for periode in periodes:
            valeurs = simulation_actuelle.calculate(calcul, periode)
            sources = simulation_actuelle.calculate(calcul, ref_periode)

            print (numpy.histogram(valeurs - sources))
            print(100.0 * sum((abs(valeurs - sources) < threshold)) / len(sources))

            results[calcul + ref_periode] = sources
            results[calcul + periode] = valeurs
            results[calcul + 'adiff'] = abs(sources - valeurs)

            results = results.sort_values(by=[calcul + 'adiff'], ascending=False)
            print(results)


    if len(limitedIds) == 1:
        simulation_actuelle.tracer.print_computation_log()
        pprint(situations)

    outpath = getPath(key='out', ext=timestamp + '.csv')
    print(outpath)
    results.to_csv(outpath, index=False, decimal=",", sep=";")


if __name__ == '__main__':
    sys.exit(main())
