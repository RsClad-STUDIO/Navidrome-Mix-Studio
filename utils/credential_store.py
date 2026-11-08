"""Windows Credential Managerを利用した認証情報ストレージ。"""

import ctypes
import os
from ctypes import wintypes


class CredentialStoreError(RuntimeError):
    """OSの資格情報ストアを利用できない場合の例外。"""


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class _CREDENTIALW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", _FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


class WindowsCredentialStore:
    """WindowsユーザーのCredential ManagerにGeneric Credentialを保存します。"""

    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2
    ERROR_NOT_FOUND = 1168

    @staticmethod
    def _api():
        if os.name != "nt":
            raise CredentialStoreError(
                "Windows Credential Manager is available only on Windows."
            )
        try:
            api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
            api.CredWriteW.argtypes = [ctypes.POINTER(_CREDENTIALW), wintypes.DWORD]
            api.CredWriteW.restype = wintypes.BOOL
            api.CredReadW.argtypes = [
                wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                ctypes.POINTER(ctypes.POINTER(_CREDENTIALW)),
            ]
            api.CredReadW.restype = wintypes.BOOL
            api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
            api.CredDeleteW.restype = wintypes.BOOL
            api.CredFree.argtypes = [ctypes.c_void_p]
            api.CredFree.restype = None
            return api
        except Exception as exc:
            raise CredentialStoreError(
                f"Windows Credential Manager could not be initialized: {exc}"
            ) from exc

    def set_password(self, target: str, password: str) -> None:
        if not target:
            raise ValueError("Credential target must not be empty.")
        blob = password.encode("utf-8")
        if len(blob) > 2560:
            raise CredentialStoreError("Credential exceeds the Windows 2560-byte limit.")

        api = self._api()
        buffer = ctypes.create_string_buffer(blob) if blob else None
        credential = _CREDENTIALW()
        credential.Type = self.CRED_TYPE_GENERIC
        credential.TargetName = target
        credential.CredentialBlobSize = len(blob)
        credential.CredentialBlob = (
            ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)) if buffer else None
        )
        credential.Persist = self.CRED_PERSIST_LOCAL_MACHINE
        credential.UserName = ""
        if not api.CredWriteW(ctypes.byref(credential), 0):
            error = ctypes.get_last_error()
            raise CredentialStoreError(
                f"Credential Manager write failed (Windows error {error})."
            )

    def get_password(self, target: str):
        if not target:
            return None
        api = self._api()
        pointer = ctypes.POINTER(_CREDENTIALW)()
        if not api.CredReadW(
            target, self.CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)
        ):
            error = ctypes.get_last_error()
            if error == self.ERROR_NOT_FOUND:
                return None
            raise CredentialStoreError(
                f"Credential Manager read failed (Windows error {error})."
            )
        try:
            credential = pointer.contents
            raw = (
                ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
                if credential.CredentialBlobSize
                else b""
            )
            return raw.decode("utf-8")
        except Exception as exc:
            raise CredentialStoreError(
                f"Stored credential could not be decoded: {exc}"
            ) from exc
        finally:
            api.CredFree(pointer)

    def delete_password(self, target: str) -> None:
        if not target:
            return
        api = self._api()
        if not api.CredDeleteW(target, self.CRED_TYPE_GENERIC, 0):
            error = ctypes.get_last_error()
            if error != self.ERROR_NOT_FOUND:
                raise CredentialStoreError(
                    f"Credential Manager delete failed (Windows error {error})."
                )
