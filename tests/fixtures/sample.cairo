#[contract]
mod Hello {
    #[abi(embed_v0)]
    impl HelloImpl of IHello<ContractState> {
        fn greet(self: @ContractState) -> felt252 {
            'Hello'
        }
    }
}
