from dataclasses import dataclass


@dataclass
class Mode:
    name: str
    code: int
    permission: int


# complete system access, for development and debugging
ADMIN_MODE = Mode(name='admin', code=0, permission=0)

# full access to control parameters, for common main user tasks
OPERATOR_MODE = Mode(name='operator', code=1, permission=1)

# read access to temperature parameters and write access to temperature set point
LEAD_MODE = Mode(name='lead', code=2, permission=2)

# read access to temperature
FOLLOW_MODE = Mode(name='follow', code=3, permission=3)

# no api key required
UNAUTHENTICATED_MODE = Mode(name='unauthenticated', code=99, permission=99)
