from argparse import ArgumentParser
from spade import wait_until_finished, run
from AgentAutomat import AgentAutomat
from AgentCovjek import AgentCovjek

async def pokreniSkriptu(brojLjudi):
    automat_agent = AgentAutomat(jid="agentAutomat@localhost", password="agentAutomat")
    await automat_agent.start()
    
    for redniBroj in range(brojLjudi):
        print("Pokrećem agenta za osobu broj:", redniBroj + 1)
        while True:
            unosBudzet = input("Koliki je saldo? ")
            try:
                iznosBudzet = float(unosBudzet)
                if iznosBudzet < 10:
                    print("Saldo mora biti veći od 10.")
                else:
                    break
            except ValueError:
                print("Krivi unos, probaj opet.")
        covjek_agent = AgentCovjek(jid=f"agentCovjek{redniBroj + 1}@localhost", password=f"agentCovjek{redniBroj + 1}", budzet=iznosBudzet)
        await covjek_agent.start()
        await wait_until_finished(covjek_agent)
        
    await automat_agent.stop()
    print("Završavam rad automata.")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-brojLjudi", type=int, help="Koliko ljudi (agenata) će koristiti automat?")
    args = parser.parse_args()
    run(pokreniSkriptu(args.brojLjudi))