# -*- coding: utf-8 -*-

from openfisca_core import reforms, periods
from openfisca_france.model.base import *


class CPAMReform(reforms.Reform):
    class cmu_base_ressources(Variable):
        value_type = float
        label = u"Base de ressources prise en compte pour l'éligibilité à la CMU-C / ACS"
        entity = Famille
        definition_period = MONTH

        def formula(famille, period, parameters):
            previous_year = period.start.period('year').offset(-1)

            ressources_famille_a_inclure = [
                'af',
                'asf',
                'aspa',
                'cf',
                'paje_clca',
                'paje_prepare',
                ]

            ressources_famille = sum([
                famille(ressource, previous_year, options = [ADD])
                for ressource in ressources_famille_a_inclure
                ])

            statut_occupation_logement = famille.demandeur.menage('statut_occupation_logement', period)
            cmu_forfait_logement_base = famille('cmu_forfait_logement_base', period)
            cmu_forfait_logement_al = famille('cmu_forfait_logement_al', period)

            P = parameters(period).cmu

            proprietaire = (statut_occupation_logement == TypesStatutOccupationLogement.proprietaire)
            heberge_titre_gratuit = (statut_occupation_logement == TypesStatutOccupationLogement.loge_gratuitement)

            forfait_logement = (
                (proprietaire + heberge_titre_gratuit)
                * cmu_forfait_logement_base
                + cmu_forfait_logement_al
                )

            ressources_individuelles = famille.members('cmu_base_ressources_individu', period)
            ressources_parents = famille.sum(ressources_individuelles, role = Famille.PARENT)

            age = famille.members('age', period)
            condition_enfant_a_charge = (age >= 0) # * (age <= P.age_limite_pac)
            ressources_enfants = famille.sum(ressources_individuelles * condition_enfant_a_charge, role = Famille.ENFANT)

            return forfait_logement + ressources_famille + ressources_parents + ressources_enfants


    def apply(self):
        self.update_variable(self.cmu_base_ressources)
