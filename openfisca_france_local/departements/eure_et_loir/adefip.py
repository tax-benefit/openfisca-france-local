 # -*- coding: utf-8 -*-
from numpy import logical_not as not_, select

from openfisca_france.model.base import Variable, Enum, Individu, MONTH

class eure_et_loir_adefip_versee(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = u"AdéFIP versée en une fois dans les 12 derniers mois"

class TypesRepriseActivite(Enum):
    adefip_invalide = "Reprise d'activité invalide au sens de l'éligibilité AdéFIP Eure-et-Loir"
    formation = "En formation de 3 mois ou plus"
    cdd_plus_3mois = "CDD de 3 à 6 mois"
    cdd_plus_6mois = "CDD de plus de 6 mois"
    cdi_temps_plein = "CDI à temps plein"
    cdi_temps_partiel = "CDI à temps partiel et supérieure à 15h par semaine"
    entreprise = "Création ou reprise d'entreprise"


class formation(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = "En formation de 3 mois ou plus"
    reference = "./sources_du_droit/departements/eure_et_loir/adefip/Réglement Departemental RSA-AdéFIP.pdf"
    documentation = '''
    Pour l'AdéFIP Eure-et-Loir, formations à temps complet,
    les visas ne sont pas pris en compte ainsi que les formations par correspondance.
    '''


class entreprise(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = "Création ou reprise d'entreprise dans les 6 derniers mois"
    reference = "./sources_du_droit/departements/eure_et_loir/adefip/Réglement Departemental RSA-AdéFIP.pdf"


class eure_et_loir_adefip_reprise_activite(Variable):
    value_type = Enum
    default_value = TypesRepriseActivite.adefip_invalide
    possible_values = TypesRepriseActivite
    entity = Individu
    label = "Situations de reprise d'activité au sens de l'AdéFIP Eure-et-Loir"
    definition_period = MONTH

    def formula(individu, period):
        formation = individu("formation", period)
        contrat_de_travail_duree = individu("contrat_de_travail_duree", period)  # cdi, cdd

        contrat_de_travail_duree_mois = individu("contrat_de_travail_duree_mois", period)
        contrat_plus_3mois = contrat_de_travail_duree_mois >= 3
        contrat_plus_6mois = contrat_de_travail_duree_mois >= 6

        contrat_de_travail = individu("contrat_de_travail", period)  # temps_plein, temps_partiel

        heures_remunerees_volume = individu("heures_remunerees_volume", period)
        semaine_15h_min = heures_remunerees_volume >= (15 * 4)

        entreprise = individu("entreprise", period)

        return select(
            [
                formation,
                (contrat_de_travail_duree == 'cdd') * contrat_plus_3mois * not_(contrat_plus_6mois),
                (contrat_de_travail_duree == 'cdd') * contrat_plus_6mois,
                (contrat_de_travail_duree == 'cdi') * (contrat_de_travail == 'temps_plein'),
                (contrat_de_travail_duree == 'cdi') * (contrat_de_travail == 'temps_partiel') * semaine_15h_min,
                entreprise
                ],
            [
                TypesRepriseActivite.formation,
                TypesRepriseActivite.cdd_plus_3mois,
                TypesRepriseActivite.cdd_plus_6mois,
                TypesRepriseActivite.cdi_temps_plein,
                TypesRepriseActivite.cdi_temps_partiel,
                TypesRepriseActivite.entreprise
                ]
        )


class eure_et_loir_eligibilite_adefip(Variable):
    value_type = bool
    entity = Individu
    definition_period = MONTH
    label = "Éligibilité à l'AdéFIP"
    documentation = '''
    AdéFIP : aide financière destinée aux personnes bénéficiaires du RSA qui reprennent une
    activité professionnelle ou qui entament une formation.

    Cette aide devra intervenir au plus tard dans les quatre mois du fait générateur de la demande
    (prise d’emploi ou formation), ou dans les 6 mois maximum pour les créations/reprises d’entreprise.

    Une seule aide peut être accordée par période de 12 mois, sauf dérogation laissée à la discrétion
    du président du Conseil départemental (Ex : Succession de CDD) avec un plafond annuel ne
    pouvant dépasser 1 000 €.
    '''

    def formula(individu, period):
        reside_eure_et_loir = individu.menage('eure_et_loir_eligibilite_residence', period)
        recoit_rsa = individu.famille('rsa', period) > 0
        cer = individu('cer', period)
        ppae = individu('ppae', period)
        eure_et_loir_adefip_versee = individu('eure_et_loir_adefip_versee', period)
        eure_et_loir_adefip_reprise_activite = individu('eure_et_loir_adefip_reprise_activite', period)

        return (
            reside_eure_et_loir * not_(eure_et_loir_adefip_versee) 
            * recoit_rsa
            * (cer + ppae)
            * (eure_et_loir_adefip_reprise_activite != TypesRepriseActivite.adefip_invalide)
            )


class eure_et_loir_montant_adefip(Variable):
    value_type = float
    entity = Individu
    definition_period = MONTH
    label = "Montant de l'AdéFIP"
    documentation = '''
    Cette aide est versée sous forme de bourses forfaitaires afin de faire face très rapidement aux
    premières dépenses et aux besoins de trésorerie des bénéficiaires du RSA qui reprennent une
    activité.

    L'aide est versée en une seule fois.
    '''

    def formula(individu, period, parameters):
        eure_et_loir_eligibilite_adefip = individu("eure_et_loir_eligibilite_adefip", period)
        eure_et_loir_adefip_reprise_activite = individu("eure_et_loir_adefip_reprise_activite", period)

        bareme = parameters(period).departements.eure_et_loir.adefip.montant
        montant = select(
            [
                eure_et_loir_adefip_reprise_activite == TypesRepriseActivite.formation,
                eure_et_loir_adefip_reprise_activite == TypesRepriseActivite.cdd_plus_3mois,
                eure_et_loir_adefip_reprise_activite == TypesRepriseActivite.cdd_plus_6mois,
                eure_et_loir_adefip_reprise_activite == TypesRepriseActivite.cdi_temps_plein,
                eure_et_loir_adefip_reprise_activite == TypesRepriseActivite.cdi_temps_partiel,
                eure_et_loir_adefip_reprise_activite == TypesRepriseActivite.entreprise
                ],
            [
                bareme.formation,
                bareme.cdd.plus_3_mois,
                bareme.cdd.plus_6_mois,
                bareme.cdi.temps_plein,
                bareme.cdi.temps_partiel,
                bareme.entreprise
                ]
        )
        return eure_et_loir_eligibilite_adefip * montant
