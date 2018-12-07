# -*- coding: utf-8 -*-
from openfisca_core.simulations import Simulation
import openfisca_france


from pprint import pprint
import codecs
import re
import sys

from openfisca_core.periods import period

# find *.csv -type f -exec iconv -f iso-8859-1 -t utf-8 "{}" -o "{}"utf8.csv \;

def getPath(key, ext=''):
    return sys.argv[-1].format(key) + ext

def getMonth(string):
    return re.sub('^(?P<jour>\d{2})/(?P<mois>\d{2})/(?P<annee>\d{4})$', '\g<annee>-\g<mois>', string)

situations = {
  'individus': {},
  'familles': {},
  'foyers_fiscaux': {},
  'menages': {},
}

def main():
    tax_benefit_system = openfisca_france.CountryTaxBenefitSystem()

    periode = '2018-11'
    ref_periode = '2017-11'
    periode_1 = '2018-10'
    months = period('year:2018-11').offset(-1, 'year').get_subperiods('month')

    periodes = [periode]
    calculs = {
        'ppa': periodes,
    }

    import csv

    limitedIds = []
    n_limit = 3

    import datetime
    now = datetime.datetime.now()
    timestamp = now.isoformat().replace(':','-').replace('.', '-')

    with open(getPath('DRT')) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        n = 0
        for row in reader:
            MATRICUL = row['MATRICUL']

            if len(limitedIds) and MATRICUL not in limitedIds:
                continue

            if row['NATPF'] != 'PPA' or row['MOISDROV'] != '01/11/2018':
                continue

            n = n + 1
            if n > n_limit:
                break

            situations['familles'][MATRICUL] = {
                'parents': [],
                'enfants': [],
                'ppa': {
                    ref_periode: row['MTDROVAL']
                },
                'rsa_nb_enfants': {},
                'af': {},
                'af_base': {},
                'ppa_forfait_logement': {},
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

            situations['individus'][demandeur] = {}
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

            # Hack current implementation where rsa_nb_enfants and ppa_forfait_logement are looked at periode instead of in the past
            situations['familles'][MATRICUL]['af'][periode] = row['MTPFPAF']
            situations['familles'][MATRICUL]['af_base'][periode] = row['MTPFPAF']
            situations['familles'][MATRICUL]['ppa_forfait_logement'][periode] = row['MTFLOPAF']

    print(n)

    ressourceMapping = {
        'Revenus d\'activité salariée': 'salaire_net',
        'Revenus du patrimoine. Spécifique PPA': 'revenus_locatifs'
    }

    with open(getPath('RSM')) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        n = 0
        for row in reader:
            MATRICUL = row['MATRICUL']

            if MATRICUL not in situations['menages']:
                continue

            if row['NATRESS'] == 'Ressources nulles':
                continue
            n = n + 1

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
            ressource = ressourceMapping[row['NATRESS']]
            montant = float(row['MTNRESSM'].replace(',', '.'))

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
            sources = simulation_actuelle.calculate(calcul, ref_periode)

            print (numpy.histogram(valeurs - sources))
            print(100.0 * sum((sources != 0) * (abs(valeurs - sources) < threshold)) / sum(sources != 0))

            results[calcul + ref_periode] = sources
            results[calcul + periode] = valeurs
            results[calcul + 'adiff'] = abs(sources - valeurs)

            results = results.sort_values(by=[calcul + 'adiff'], ascending=False)
            print(results)


    if len(limitedIds) == 1:
        pprint(situations)
        simulation_actuelle.tracer.print_computation_log()

    #outpath = getPath(key='', ext=timestamp + '.out.csv')
    #print(outpath)
    #results.to_csv(outpath, index=False, decimal=",", sep=";")


if __name__ == '__main__':
    sys.exit(main())
