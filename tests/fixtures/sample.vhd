entity hello is
end entity hello;

architecture behavioral of hello is
begin
  process
  begin
    report "Hello";
    wait;
  end process;
end architecture behavioral;
