from openfisca_france.model.base import Individu, MONTH, Variable, ADD

class auvergne_rhone_alpes_aide_permis(Variable):
    value_type = float
    entity = Individu
    label = "Montant de l'aide au permis de conduire pour la région Auvergne-Rhône-Alpes."
    reference = "https://www.auvergnerhonealpes.fr/aide/385/289-financer-ma-formation-au-permis-de-conduire-orientation-formation.htm#thema146"
    definition_period = MONTH

    def formula(individu, period, parameters):
        params = parameters(period).regions.auvergne_rhone_alpes.aide_permis

        montant = params.montant

        eligibilite_residentielle = individu.menage("auvergne_rhone_alpes_eligibilite_residence", period)

        eligibilite_age = individu('age', period) == params.age

        return eligibilite_residentielle * eligibilite_age * montant
