from openfisca_core.populations import ADD
from openfisca_france.model.base import Variable, Individu, Menage, MONTH, not_, TypesActivite


class aide_poursuite_etudes_eligibilite(Variable):
    value_type = float
    entity = Individu
    label = "Éligibilité financière à l'aide à l’obtention du permis de conduire"
    reference = [
        "https://www.hautsdefrance.fr/aide-au-permis-de-conduire/"
    ]
    definition_period = MONTH

    def formula(individu, period, parameters):
        eligibilite_activite = individu('etudiant', period)

        age = individu('age', period)
        eligibilite_age = (age >= parameters(period).regions.bretagne.aide_poursuite_etudes.age_minimal) * (age <= parameters(period).regions.bretagne.aide_poursuite_etudes.age_maximum)

        salaire = individu('salaire_net', period.last_3_months, options=[ADD])
        smic_proratise = individu('smic_proratise', period)

        eligibilite_ressources = (salaire) < ((smic_proratise * parameters(period).regions.bretagne.aide_poursuite_etudes.seuil_ressources) * 3)

        return eligibilite_age * eligibilite_activite * eligibilite_ressources


class aide_poursuite_etudes(Variable):
    value_type = float
    entity = Individu
    label = "Éligibilité financière à l'aide à l’obtention du permis de conduire"
    reference = [
        "https://www.hautsdefrance.fr/aide-au-permis-de-conduire/"
    ]
    definition_period = MONTH

    def formula(individu, period, parameters):
        eligibilite = individu("aide_poursuite_etudes_eligibilite", period)
        return eligibilite * 1000