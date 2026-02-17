from typing import Any

from core.message import ErrorDetail


class AppException(Exception):
    def __init__(self, detail: ErrorDetail, **kwargs: Any):
        self.detail = detail
        self.http_status = detail.http_status
        self.code = detail.code

        # Tentative de formatage du message avec les arguments passés
        try:
            self.message = detail.message.format(**kwargs)
        except KeyError as e:
            # Sécurité si une variable attendue dans le template est oubliée
            self.message = f"{detail.message} (Missing context: {e})"
        except ValueError as e:
            # Sécurité spécifique : problème de type ou de syntaxe dans le formatage
            self.message = f"{detail.message} (Format error: {e})"
        super().__init__(self.message)
