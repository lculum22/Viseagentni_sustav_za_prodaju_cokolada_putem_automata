from spade.agent import Agent
from asyncio import sleep
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import json

class AgentCovjek(Agent):
    
    def __init__(self, jid, password, budzet):
        super().__init__(jid, password)
        self.budzet = budzet
        self.uneseniNovac = 0.0
        
    async def setup(self):
        fsm = self.CovjekPonasanje()

        fsm.add_state(name="Pocetak", state=self.Pocetak(), initial=True)
        fsm.add_state(name="IzborProizvoda", state=self.IzborProizvoda())
        fsm.add_state(name="Uplata", state=self.Uplata())
        fsm.add_state(name="CekanjeIsporuke", state=self.CekanjeIsporuke())
        fsm.add_state(name="PreuzimanjeProizvoda", state=self.PreuzimanjeProizvoda())

        fsm.add_transition(source="Pocetak", dest="IzborProizvoda")
        fsm.add_transition(source="IzborProizvoda", dest="IzborProizvoda")
        fsm.add_transition(source="IzborProizvoda", dest="Uplata")
        fsm.add_transition(source="Uplata", dest="CekanjeIsporuke")
        fsm.add_transition(source="CekanjeIsporuke", dest="CekanjeIsporuke")
        fsm.add_transition(source="CekanjeIsporuke", dest="IzborProizvoda")
        fsm.add_transition(source="CekanjeIsporuke", dest="PreuzimanjeProizvoda")
        fsm.add_transition(source="PreuzimanjeProizvoda", dest="PreuzimanjeProizvoda")
        fsm.add_transition(source="PreuzimanjeProizvoda", dest="Pocetak")

        self.add_behaviour(fsm)
    
    class CovjekPonasanje(FSMBehaviour):
        async def on_start(self):
            print("Covjek: Počinjem s radom.")
            print("Covjek: Stigao sam do automata.")

        async def on_end(self):
            print("Covjek: Završavam rad.")
            await self.agent.stop()

    class Pocetak(State):
        async def run(self):
            poruka = Message(to="agentAutomat@localhost", body=json.dumps({"porukaPocetak": True}), metadata={"ontology": "agent"})
            await self.send(poruka)
            self.set_next_state("IzborProizvoda")
            
    class IzborProizvoda(State):
        async def run(self):
            poruka = await self.receive(timeout=15)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "sviProizvodi" in sadrzajPoruke:
                    sviProizvodi = sadrzajPoruke["sviProizvodi"]
                    vrsteProizvoda = list(sviProizvodi["Cijene"].keys())
                    print("Automat nudi sljedeće proizvode: \n")
                    formatiranjeIspisa = "{:<20} {:<15} {:<10}"
                    formatiranjeRedaka = "{:<20} {:<15.2f} {:<10} Odaberi {}"
                    print(formatiranjeIspisa.format("ČOKOLADA", "CIJENA", "KOLIČINA"))
                    for index, vrsta in enumerate(vrsteProizvoda, start=1):
                        print(formatiranjeRedaka.format(
                            vrsta,
                            sviProizvodi['Cijene'][vrsta],
                            sviProizvodi['Kolicine'][vrsta],
                            index
                        ))
                    print("Odaberi 0 za odustajanje")
                    while True:
                        odabir = input("\nUnesi broj čokolade: ")
                        try:
                            odabirBroj = int(odabir)
                            if odabirBroj == 0:
                                break
                            if 1 <= odabirBroj <= len(vrsteProizvoda):
                                odabraniProizvod = vrsteProizvoda[odabirBroj - 1]
                                if sviProizvodi['Kolicine'][odabraniProizvod] > 0:
                                    break
                                else:
                                    print("Nema te čokolade, izaberi drugu.")
                            else:
                                print("Neispravan unos.")
                        except ValueError:
                            print("Neispravan unos.")
                    
                    if odabirBroj > 0:
                        while True:
                            odabirKolicine = input("Unesi količinu čokolade: ")
                            try:
                                kolicina = int(odabirKolicine)
                                if 1 <= kolicina <= sviProizvodi['Kolicine'][odabraniProizvod]:
                                    print(f"Covjek: Odabrao sam {kolicina} {odabraniProizvod}")
                                    break
                                else:
                                    print(f"Nema dovoljno {odabraniProizvod}.")
                            except ValueError:
                                print("Neispravan unos.")
                        porukaIzbor = Message(
                            to="agentAutomat@localhost",
                            body=json.dumps({
                                "porukaIzboraVrstaProizvoda": odabraniProizvod,
                                "porukaIzboraKolicinaProizvoda": kolicina
                            }),
                            metadata={"ontology": "agent"}
                        )
                        #print("Covjek: Saljem poruku: ", porukaIzbor.body)
                        await self.send(porukaIzbor)
                        self.set_next_state("Uplata")
                    else:
                        porukaKraj = Message(to="agentAutomat@localhost", body=json.dumps({"kraj": True}), metadata={"ontology": "agent"})
                        await self.send(porukaKraj)
                        print("Covjek: Odustao sam od kupnje.")
                        await self.agent.stop()
                else:
                    print("Covjek: Neispravan sadržaj poruke.")
                    self.set_next_state("IzborProizvoda")
            else:
                print("Covjek: Nema poruke nakon 15 sekundi.")
                self.set_next_state("IzborProizvoda")
                
    class Uplata(State):
        async def run(self):
            #print("UPLATA POKRENUTA")
            while True:
                await sleep(0.5)
                unosNovca = input("Unesi iznos novca: ")
                try:
                    iznosNovca = float(unosNovca)
                    if 0 < iznosNovca <= self.agent.budzet:
                        break
                    else:
                        print("Neispravan iznos ili nemaš dovoljno novca.")
                except ValueError:
                    print("Neispravan unos.")
            self.agent.uneseniNovac = iznosNovca
            await sleep(1)
            porukaUplata = Message(to="agentAutomat@localhost", body=json.dumps({"novac": iznosNovca}), metadata={"ontology": "agent"})
            await self.send(porukaUplata)
            self.set_next_state("CekanjeIsporuke")
            
    class CekanjeIsporuke(State):
        async def run(self):
            poruka = await self.receive(timeout=15)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "DovoljnoNovaca" in sadrzajPoruke:
                    if sadrzajPoruke["DovoljnoNovaca"]:
                        self.set_next_state("PreuzimanjeProizvoda")
                    else:
                        self.set_next_state("IzborProizvoda")
                else:
                    print("Covjek: Neispravan sadržaj poruke.")
                    self.set_next_state("CekanjeIsporuke")
            else:
                print("Covjek: Nema poruke nakon 15 sekundi.")
                self.set_next_state("CekanjeIsporuke")
                
    class PreuzimanjeProizvoda(State):
        async def run(self):
            poruka = await self.receive(timeout=15)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "Ostatak" in sadrzajPoruke:
                    ostatakNovca = sadrzajPoruke["Ostatak"]
                    print("Covjek: Preuzeo sam čokoladu.")
                    if ostatakNovca > 0:
                        print(f"Covjek: Vraćen mi je ostatak novca: {ostatakNovca}")
                    self.agent.budzet -= self.agent.uneseniNovac - ostatakNovca
                    print(f"Trenutni saldo: {self.agent.budzet:.2f}")
                else:
                    print("Covjek: Neispravan sadržaj poruke.")
                    self.set_next_state("PreuzimanjeProizvoda")
            else:
                print("Covjek: Nema poruke nakon 15 sekundi.")
                self.set_next_state("PreuzimanjeProizvoda")

            ponovnaKupnja = input("Želiš li još kupovati? Da ILI Ne: ")
            if ponovnaKupnja.lower() == "da":
                await sleep(2)
                self.set_next_state("Pocetak")
            else:
                print("Covjek: Odlazim.")
                await self.agent.stop()

