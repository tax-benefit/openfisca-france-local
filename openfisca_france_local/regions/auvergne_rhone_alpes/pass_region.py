 # -*- coding: utf-8 -*-
from openfisca_france.model.base import Variable, FoyerFiscal, Individu, MONTH, YEAR
 from openfisca_france.model.prestations.education import TypesScolarite


class auvergne_rhone_alpes_pass_region_eligibilite(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = u"Éligibilité à la carte Pass' Région pour la région Auvergne Rhône Alpes"

    def formula(individu, period, parameters):

        scolarite = individu('scolarite', period)
        scolaire = (scolarite == TypesScolarite.lycee)

        age = individu('age', period) >= 16 * individu('age', period) <= 25

        return scolaire * age

class auvergne_rhone_alpes_pass_region(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = u"Éligibilité à la carte Pass' Région pour la région Auvergne Rhône Alpes"

    def formula(individu, period, parameters):
        individu('auvergne_rhone_alpes_pass_region_eligibilite', period)




