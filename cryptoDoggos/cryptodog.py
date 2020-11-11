from iconservice import *

TAG = 'Dog'

class TokenStandard(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def symbol(self) -> str:
        pass

    @abstractmethod
    def balanceOf(self, _owner: Address) -> int:
        pass

    @abstractmethod
    def ownerOf(self, _tokenId: str) -> Address:
        pass

    @abstractmethod
    def getApproved(self, _tokenId: str) -> Address:
        pass

    @abstractmethod
    def approve(self, _to: Address, _tokenId: str):
        pass

    @abstractmethod
    def transfer(self, _to: Address, _tokenId: str):
        pass

    @abstractmethod
    def transferFrom(self, _from: Address, _to: Address, _tokenId: str):
        pass

    class CryptoDog(IconScoreBase, TokenStandard):
        _OWNED_TOKEN_COUNT = 'owned_token_count'  # Track token count against token owners
        _TOKEN_OWNER = 'token_owner'  # Track token owner against token ID
        _TOKEN_APPROVALS = 'token_approvals'  # Track token approved owner against token ID

        _ZERO_ADDRESS = Address.from_prefix_and_int(AddressPrefix.EOA, 0)

        def __init__(self, db: IconScoreDatabase) -> None:
            super().__init__(db)
            self._ownedTokenCount = DictDB(self._OWNED_TOKEN_COUNT, db, value_type=int)
            self._tokenOwner = DictDB(self._TOKEN_OWNER, db, value_type=Address)
            self._tokenApprovals = DictDB(self._TOKEN_APPROVALS, db, value_type=Address)

        def on_install(self) -> None:
            super().on_install()

        def on_update(self) -> None:
            super().on_update()

        def _transfer(self, _from: Address, _to: Address, _tokenId: int):
            if _to is None or self._is_zero_address(_to):
                revert("You can't transfer to a zero address")
            self._clear_approval(_tokenId)
            self._remove_tokens_from(_from, _tokenId)
            self._add_tokens_to(_to, _tokenId)
            self.Transfer(_from, _to, _tokenId)
            Logger.debug(f'Transfer({_from}, {_to}, {_tokenId}, TAG)')

        def _burn(self, _owner: Address, _tokenId: int):
            self._clear_approval(_tokenId)
            self._remove_tokens_from(_owner, _tokenId)
            self.Transfer(_owner, self._ZERO_ADDRESS, _tokenId)

        def _is_zero_address(self, _address: Address) -> bool:
            if _address == self._ZERO_ADDRESS:
                return True
            return False

        def _ensure_positive(self, _tokenId: int):
            if _tokenId is None or _tokenId < 0:
                revert("tokenId should be positive")

        def _clear_approval(self, _tokenId: int):
            if _tokenId in self._tokenApprovals:
                del self._tokenApprovals[_tokenId]

        def _remove_tokens_from(self, _from: Address, _tokenId: int):
            self._ownedTokenCount[_from] -= 1
            self._tokenOwner[_tokenId] = self._ZERO_ADDRESS

        def _add_tokens_to(self, _to: Address, _tokenId: int):
            self._tokenOwner[_tokenId] = _to
            self._ownedTokenCount[_to] += 1

        @external(readonly=True)
        def name(self) -> str:
            return "CryptoDog"

        @external(readonly=True)
        def symbol(self) -> str:
            return "CTD"

        @external(readonly=True)
        def balanceOf(self, _owner: Address) -> int:
            if _owner is None or self._is_zero_address(_owner):
                revert("Invalid owner")
            return self._ownedTokenCount[_owner]

        @external(readonly=True)
        def ownerOf(self, _tokenId: int) -> Address:
            self._ensure_positive(_tokenId)
            owner = self._tokenOwner[_tokenId]
            if owner is None:
                revert("Invalid _tokenId. NFT is not minted")
            if self._is_zero_address(owner):
                revert("Invalid _tokenId. NFT is burned")
            return owner

        @external(readonly=True)
        def getApproved(self, _tokenId: int) -> Address:
            self.ownerOf(_tokenId) 
            addr = self._tokenApprovals[_tokenId]
            if addr is None:
                return self._ZERO_ADDRESS
            return addr

        @external
        def approve(self, _to: Address, _tokenId: int):
            owner = self.ownerOf(_tokenId)
            if _to == owner:
                revert("Can't approve to yourself.")
            if self.msg.sender != owner:
                revert("You do not own this NFT")

            self._tokenApprovals[_tokenId] = _to
            self.Approval(owner, _to, _tokenId)

        @external
        def transfer(self, _to: Address, _tokenId: int):
            if self.ownerOf(_tokenId) != self.msg.sender:
                revert("You don't have permission to transfer this NFT")
            self._transfer(self.msg.sender, _to, _tokenId)

        @external
        def transferFrom(self, _from: Address, _to: Address, _tokenId: int):
            if self.ownerOf(_tokenId) != self.msg.sender and self._tokenApprovals[_tokenId] != self.msg.sender:
                revert("You don't have permission to transfer this NFT")
            self._transfer(_from, _to, _tokenId)

        @external
        def mint(self, _to: Address, _tokenId: int):
            if self.msg.sender != self.owner:
                revert("You don't have permission to mint NFT")
            if _tokenId in self._tokenOwner:
                revert("Token already exists")
            self._add_tokens_to(_to, _tokenId)
            self.Transfer(self._ZERO_ADDRESS, _to, _tokenId)

        @external
        def burn(self, _tokenId: int):
            if self.ownerOf(_tokenId) != self.msg.sender:
                revert("You dont have permission to burn this NFT")
            self._burn(self.msg.sender, _tokenId)

        @eventlog(indexed=3)
        def Approval(self, _owner: Address, _approved: Address, _tokenId: int):
            pass

        @eventlog(indexed=3)
        def Transfer(self, _from: Address, _to: Address, _tokenId: int):
            pass