# CATEGORYS ARE DICTIONARIES//
# WEAPONS INDEXED AS Weapons["ITEM"][X]// (X) 0 =DMG, 1 = FIRE-RATE, 2 = AMMO_TYPE
# ARMOR IS INDEXED AS Armor["ITEM"][X]// (X) 0 =SLOT, 1 = DAMAGE REDUCTION
# AMMO IS INDEXED AS Ammo["ITEM"][X]// (X) 0 = SPEED, 1=  PENETRATION VALUE
# CONSUMABLES IS INDEXED AS Consumables["ITEM"][X]// (X) 0 = EFFECT, 1 =AMOUNT
# MISC IS INDEXED AS Misc["ITEM"][X]// (X) 0 = Description

Weapons = {
    "SMG": ("smg.png", 7, 0.1, "9mm Ammo"),
    "Bat": ("bat.png", 2, 5, None),
    "Pistol": ("pistol.png", 5, 1, "9mm Ammo"),
    "Machete": ("machete.png", 8, 3,None),
    "Shotgun": ("shotgun.png", 25, 1.5, "Shotgun Shells"),
    "Rifle": ("rifle.png", 10, 0.2, "5.56mm Ammo"),
    "Sniper Rifle": ("heavysnipe.png", 50, 2.0, "50cal Ammo")
}
Armor = {
    "Hat": ("hat.png", "H", 1),
    "Crocs": ("crocs.png", "F", 1),
    "Shirt": ("shirt.png", "C", 1),
    "Combat Helmet": ("helmet.png", "H", 5),
    "Combat Chestplate": ("cchest.png", "C", 10),
    "Combat Boots": ("cboots.png", "F", 5),
    "T-45 Power Armor Helmet": ("t45h.png", "H", 15),
    "T-45 Power Armor Chestplate": ("t45c.png", "C", 30),
    "T-45 Power Armor Boots": ("t45f.png", "F", 15)
}
Ammo = {
    None: ("9mm.png", 0, None),
    "9mm Ammo": ("9mm.png", 1, 1),
    "50cal Ammo": ("50cal.png", 4, 10),
    "Shotgun Shells": ("shells.png", 2, 1),
    "5.56mm Ammo": ("5.56mm.png", 2, 2)
}
Consumables = {
    "Medkit": ("medkit.png", "HEAL", 50),
    "Bandages": ("bandages.png", "HEAL", 15),
    "Plasters": ("plasters.png", "HEAL", 5),
    "Survival Kit": ("kit.png", "HEAL", 100),
    "Coca-Cola": ("coke.png", "HEAL", 3)
}
Misc = {"Key": ("key.png",("A Rusty Key With The Word Tony Engraved")), "Lockpick": ("key.png",("Simple Lockpick")), "Cap(s)":("cap.png",("Currency Of Some Sort")),"Trophy":("trophy.png",("A Trophy From Shade To Show You Couldve Left The Wasteland But Stayed"))}
