from openfisca_france.model.base import Variable, Individu, MONTH


class cer(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = "A un Contrat d'Engagements Réciproques (CER) en cours."
    reference = "https://www.service-public.fr/particuliers/vosdroits/R43349"
    documentation = '''
    Le présent contrat est conclu pour une durée initiale d’un an.
    Il est renouvelable une fois par voie d’avenant pour une durée comprise entre un et six mois.
    '''


class ppae(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = "A un Projet Personnalisé d'Accès à l'Emploi (PPAE) en cours."
    reference = "https://www.service-public.fr/particuliers/vosdroits/F14926"


class contrat_de_travail_duree_mois(Variable):
    value_type = int
    entity = Individu
    definition_period = MONTH
    label = "Durée en mois du contrat de travail"

    def formula(individu, period):
        contrat_de_travail_debut = individu("contrat_de_travail_debut", period)
        contrat_de_travail_fin = individu("contrat_de_travail_fin", period)
        return contrat_de_travail_fin - contrat_de_travail_debut
