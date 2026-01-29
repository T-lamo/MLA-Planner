from mla_enum import RoleName

ROLES = [RoleName.ADMIN, RoleName.RESPONSABLE_MLA, RoleName.MEMBRE_MLA]

PERMISSIONS = {
    RoleName.ADMIN: [
        "USER_CREATE",
        "USER_READ",
        "USER_UPDATE",
        "USER_DELETE",
        "ROLE_MANAGE",
        "MINISTERE_MANAGE",
        "POLE_MANAGE",
        "ACTIVITE_MANAGE",
        "PERMISSION_MANAGE",
    ],
    RoleName.RESPONSABLE_MLA: [
        "USER_CREATE",
        "USER_READ",
        "USER_UPDATE",
        "MINISTERE_MANAGE",
        "POLE_MANAGE",
        "ACTIVITE_MANAGE",
    ],
    RoleName.MEMBRE_MLA: ["USER_READ", "ACTIVITE_CREATE", "ACTIVITE_UPDATE"],
}
