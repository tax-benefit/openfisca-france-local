from openfisca_france.model.base import Variable, Individu, MONTH
from numpy.core.defchararray import startswith

DEPARTEMENTS_OCCITANIE = [
    b"09", b"11", b"12", b"30", b"31", b"32", b"34", b"46", b"48", b"65", b"66", b"81", b"82"
]

class eligibilite_occitanie(Variable):
    value_type = float
    entity = Individu
    definition_period = MONTH
    label = "Eligibilité depcom à la région occitanie"

    def formula(individu, period):
        depcom = individu.menage('depcom', period)
        return sum([startswith(depcom, code_departement) for code_departement in DEPARTEMENTS_OCCITANIE])
