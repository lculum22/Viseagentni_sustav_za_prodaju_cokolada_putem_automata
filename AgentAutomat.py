from spade.agent import Agent
from asyncio import sleep
from spade.behaviour import FSMBehaviour, State
from spade.message import Message
import json

class AgentAutomat(Agent):
    
    def __init__(self, jid, password):
        super().__init__(jid, password) 
        self.proizvodi = {
            "Cijene": {
                "Milka": 3.25, 
                "Dorina": 2.5, 
                "Kinder": 3.0, 
                "Bajadera": 3.0, 
                "Nutella B-Ready": 1.2,
                "Twix": 1.4,
                "Snickers": 1.8,
                "Mars": 1.5,
                "KitKat": 1.5,
                "Ritter Sport": 2.2,
                "Lindt": 2.75,
                "Dubai": 8.50
            },
            "Kolicine": {
                "Milka": 8, 
                "Dorina": 12, 
                "Kinder": 5, 
                "Bajadera": 6, 
                "Nutella B-Ready": 7,
                "Twix": 6,
                "Snickers": 5,
                "Mars": 6,
                "KitKat": 9,
                "Ritter Sport": 10,
                "Lindt": 9,
                "Dubai": 15
            }
        }
        self.korisnikJID = ""
        self.odabranaCokolada = ""
        self.kolicinaZaKupiti = 0
        self.trenutnaCijena = 0
        self.primljeniNovac = 0

    class AutomatPonasanje(FSMBehaviour):
        async def on_start(self):
            print("Automat: Pokrećem se...")

        async def on_end(self):
            print("Automat: Završavam rad.")
            await self.agent.stop()
        
    async def setup(self):
        fsm = self.AutomatPonasanje()

        fsm.add_state(name="CekanjeKorisnika", state=self.CekanjeKorisnika(), initial=True)
        fsm.add_state(name="CekanjeIzbora", state=self.CekanjeIzbora())
        fsm.add_state(name="CekanjeUplate", state=self.CekanjeUplate())
        fsm.add_state(name="IsporukaProizvoda", state=self.IsporukaProizvoda())

        fsm.add_transition(source="CekanjeKorisnika", dest="CekanjeKorisnika")
        fsm.add_transition(source="CekanjeKorisnika", dest="CekanjeIzbora")
        fsm.add_transition(source="CekanjeIzbora", dest="CekanjeIzbora")
        fsm.add_transition(source="CekanjeIzbora", dest="CekanjeUplate")
        fsm.add_transition(source="CekanjeIzbora", dest="CekanjeKorisnika")
        fsm.add_transition(source="CekanjeUplate", dest="CekanjeUplate")
        fsm.add_transition(source="CekanjeUplate", dest="CekanjeIzbora")
        fsm.add_transition(source="CekanjeUplate", dest="IsporukaProizvoda")
        fsm.add_transition(source="IsporukaProizvoda", dest="CekanjeKorisnika")

        self.add_behaviour(fsm)

    class CekanjeKorisnika(State):
        async def run(self):
            self.agent.korisnikJID = ""
            self.agent.odabranaCokolada = ""
            self.agent.trenutnaCijena = 0
            self.agent.primljeniNovac = 0
            print("Automat: Čekam korisnika...")
            poruka = await self.receive(timeout=10)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)

                #print("Automat: Primljena poruka: ", sadrzajPoruke)
                if "porukaPocetak" in sadrzajPoruke:
                    self.agent.korisnikJID = str(poruka.sender)
                    odgovor = Message(to=self.agent.korisnikJID, body=json.dumps({"sviProizvodi": self.agent.proizvodi}), metadata={"ontology": "agent"})
                    await self.send(odgovor)
                    self.set_next_state("CekanjeIzbora")
                else:
                    print("Automat: Neispravan sadržaj poruke.")
                    self.set_next_state("CekanjeKorisnika")
            else:
                print("Automat: Nema poruke nakon 10 sekundi.")
                self.set_next_state("CekanjeKorisnika")
                
    class CekanjeIzbora(State):
        async def run(self):
            print("Automat: Čekam izbor korisnika...")
            poruka = await self.receive(timeout=50)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "porukaIzboraVrstaProizvoda" in sadrzajPoruke:
                    vrstaProizvoda = sadrzajPoruke["porukaIzboraVrstaProizvoda"] 
                    kolicinaProizvoda = sadrzajPoruke["porukaIzboraKolicinaProizvoda"] 
                    self.agent.trenutnaCijena = round(self.agent.proizvodi["Cijene"][vrstaProizvoda] * kolicinaProizvoda, 2)
                    self.agent.odabranaCokolada = vrstaProizvoda
                    self.agent.kolicinaZaKupiti = kolicinaProizvoda
                    print("Automat: Ukupna cijena je:", self.agent.trenutnaCijena)
                    self.set_next_state("CekanjeUplate")
                elif "kraj" in sadrzajPoruke:
                    self.set_next_state("CekanjeKorisnika")
                else:
                    print("Automat: Neispravan izbor.")
                    self.set_next_state("CekanjeIzbora")
            else:
                print("Automat: Nema poruke nakon 50 sekundi.")
                self.set_next_state("CekanjeIzbora")
                
    class CekanjeUplate(State):
        async def run(self):
            print("Automat: Čekam uplatu...")
            poruka = await self.receive(timeout=20)
            if poruka:
                sadrzajPoruke = json.loads(poruka.body)
                if "novac" in sadrzajPoruke:
                    kolicinaNovca = sadrzajPoruke["novac"]
                    if kolicinaNovca >= self.agent.trenutnaCijena:
                        print("Automat: Dovoljno novca primljeno.")
                        self.agent.primljeniNovac = kolicinaNovca
                        odgovor = Message(to=self.agent.korisnikJID, body=json.dumps({"DovoljnoNovaca": True}), metadata={"ontology": "agent"})
                        await self.send(odgovor)
                        self.set_next_state("IsporukaProizvoda")
                    else:
                        print("Automat: Nedovoljno novca. Vraćam novac.")
                        odgovor = Message(to=self.agent.korisnikJID, body=json.dumps({"DovoljnoNovaca": False}), metadata={"ontology": "agent"})
                        await self.send(odgovor)
                        await sleep(1)
                        ponuda = Message(to=self.agent.korisnikJID, body=json.dumps({"sviProizvodi": self.agent.proizvodi}), metadata={"ontology": "agent"})
                        await self.send(ponuda)
                        self.set_next_state("CekanjeIzbora")
                else:
                    self.set_next_state("CekanjeUplate")
            else:
                print("Automat: Nema poruke nakon 20 sekundi.")
                self.set_next_state("CekanjeUplate")
                
    class IsporukaProizvoda(State):
        async def run(self):
            print("Automat: Isporučujem:", self.agent.kolicinaZaKupiti, self.agent.odabranaCokolada)
            self.agent.proizvodi["Kolicine"][self.agent.odabranaCokolada] -= self.agent.kolicinaZaKupiti
            if self.agent.proizvodi["Kolicine"][self.agent.odabranaCokolada] < 1:
                print("Automat: Ponestalo je:", self.agent.odabranaCokolada)
                self.agent.proizvodi["Kolicine"][self.agent.odabranaCokolada] = 0
            ostatakNovca = round(self.agent.primljeniNovac - self.agent.trenutnaCijena, 2)
            if ostatakNovca > 0:
                print("Automat: Vraćam ostatak novca:", ostatakNovca)
            odgovor = Message(to=self.agent.korisnikJID, body=json.dumps({"Ostatak": ostatakNovca}), metadata={"ontology": "agent"})
            await self.send(odgovor)
            await sleep(1)
            self.set_next_state("CekanjeKorisnika")
