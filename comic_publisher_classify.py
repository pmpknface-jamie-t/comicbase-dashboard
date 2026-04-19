"""
comic_publisher_classify.py
============================
Classifies comic book titles from CB_Export_Current.txt by publisher,
then rewrites the file with a Publisher column (col 2, after Title).

Usage:
    python3 comic_publisher_classify.py

The script:
1. Reads CB_Export_Current.txt from the same directory
2. Classifies each unique title against known publisher rules
3. Saves publisher_map.json alongside the script (for inspection / manual edits)
4. Rewrites CB_Export_Current.txt with Publisher inserted after Title column
5. Reports unknowns to unknowns.txt for follow-up research

To improve classification, edit the sets/lists inside assign_publisher() below,
or add entries directly to publisher_map.json and re-run with --from-map flag.
"""

import csv, json, shutil, os, sys
from pathlib import Path
from collections import Counter

SCRIPT_DIR = Path(__file__).parent
DATA_FILE  = SCRIPT_DIR / "CB_Export_Current.txt"
MAP_FILE   = SCRIPT_DIR / "publisher_map.json"
UNKNOWN_FILE = SCRIPT_DIR / "unknowns.txt"

# ─────────────────────────────────────────────
# Publisher rule sets
# ─────────────────────────────────────────────

VERTIGO = {
    "100 Bullets","100 Bullets: Brother Lono","Aloha, Hawaiian Dick","American Freak: A Tale of the Un-Men",
    "American Virgin","Amethyst (1st Series)","Animal Man","Animal Man (2nd Series)","Anomaly",
    "Apocalypse Nerd","Aristotle and Dante Discover the Secrets of the Universe","Army@Love","Army@Love: The Art of War",
    "B.P.R.D.","Babylon 5","Bad Doctor, The","Banana Sunday","Bite Club","Black Orchid","Bloody Mary",
    "Books of Faerie, The","Books of Magic","Books of Magic (2nd Series)","Books of Magic: Life During Wartime",
    "Brother Power the Geek","Cages","Camelot 3000","Capitalist Gothic","Carpathian","Casanova",
    "Catwoman: When in Rome","Cinderella: From Fabletown with Love","Cinderella: Fables Are Forever",
    "Codename: Knockout","Crossing Midnight","Deadenders","Death: At Death's Door",
    "Death: The High Cost of Living","Death: The Time of Your Life","Destiny: A Chronicle of Deaths Foretold",
    "DMZ","DMZ (2nd Series)","Doctor 13: Architecture & Mortality","Dogs of War",
    "Doom Patrol","Doom Patrol (2nd Series)","Doom Patrol (3rd Series)","Doom Patrol (4th Series)",
    "Egypt","El Diablo","Enginehead","Enigma","Exterminators, The","Fables","Fables: The Wolf Among Us",
    "Fairest","Flinch","Flush","Goddess","Greek Street","Grip: The Strange World of Men","Hellblazer",
    "House of Mystery","House of Secrets","Human Target","Human Target: Final Cut","Human Target: Strike Zones",
    "I, Zombie","Identity Crisis","iZombie","Jack of Fables","Jonah Hex","Jonathan Strange & Mr Norrell",
    "Kid Eternity","Kill Your Boyfriend","Lucifer","Lucifer (2nd Series)","Massacre","Mazeworld",
    "Me and Edith Head","Midnight, Mass.","Midnight, Mass.: Here There Be Monsters","Mnemovore",
    "Mobfire","Moomin: The Complete Tove Jansson Comic Strip","My Faith in Frankie","My Name is Holocaust",
    "Neil Gaiman's Lady Justice","Nevada","New Romancer","New York Four, The","New York Five, The",
    "Night Force","Night Force (2nd Series)","Northlanders","Orbiter","Orion","Outlaw Nation",
    "Palestine","Paradox","Paul Pope's THB","Pete & Dud: Come Again","Peter Milligan's Greek Street",
    "Phantom Stranger","Preacher","Pride & Joy","Proposition Player","Punisher MAX",
    "Reasons to be Cheerful","Resurrection Man","Revolver","Richard Corben","Sandman",
    "Sandman (2nd Series)","Sandman Mystery Theatre","Sandman: Endless Nights",
    "Sandman: Overture","Sandman: The Dream Hunters","Sandman: The Wake","Scene of the Crime",
    "Seekers Into the Mystery","Shade, The Changing Man","Shade, The Changing Man (2nd Series)",
    "Slash Maraud","Sleeper","Sleeper: Season Two","Skreemer","Slash Maraud",
    "Sgt. Rock: The Prophecy","Solid Air","Starter for 10","Stormwatch","Strange Adventures",
    "Struggle","Swamp Thing","Swamp Thing (2nd Series)","Swamp Thing (3rd Series)",
    "Swamp Thing (4th Series)","System, The","Testament","That Damned Band","Thessaly: Witch for Hire",
    "Transmetropolitan","Trigger","True Faith","Uncle Sam","Unknown Soldier (Vertigo)",
    "V for Vendetta","Veils","Vinyl Underground","Violent Cases","Visions","Waking Hours",
    "War Story","War Stories","Wasteland","We3","Why I Hate Saturn","Winter Men, The",
    "Witching","Y: The Last Man","You Are Here",
    "99 Days",
}

DC_EXACT = {
    "52","80-Page Giant","Action Comics","Adventure Comics","Adventures of Superman",
    "Adventures of the DC Universe","Agent Liberty","All-American Comics","All Flash",
    "All Star Batman","All Star Batman and Robin, the Boy Wonder","All Star Comics",
    "All Star Squadron","All Star Superman","All Star Western","All-Flash",
    "Amethyst, Princess of Gemworld","Aquaman","Aquaman (2nd Series)","Aquaman (3rd Series)",
    "Aquaman (4th Series)","Aquaman (5th Series)","Aquaman (6th Series)","Aquaman (7th Series)",
    "Arion, Lord of Atlantis","Atari Force","Atom, The","Atom and Hawkman, The",
    "Atom: Shadow of the Atom, The","Azrael","Azrael: Agent of the Bat",
    "Aztek, the Ultimate Man","Baleman","Barren Earth","Batman","Batman & Robin",
    "Batman & Superman: World's Finest","Batman (1st Series)","Batman (2nd Series)",
    "Batman: A Death in the Family","Batman: Birth of the Demon","Batman: Blink",
    "Batman: Bride of the Demon","Batman: Castle of the Bat","Batman: Catwoman Defiant",
    "Batman: Dark Knight Dynasty","Batman: Dark Victory","Batman: Death and the Maidens",
    "Batman: Death in the City","Batman: Ego","Batman: Full Circle","Batman: Gotham Adventures",
    "Batman: Gotham by Gaslight","Batman: Gotham County Line",
    "Batman: Haunted Knight","Batman: Holy Terror","Batman: Hush",
    "Batman: I Am Suicide","Batman: In Darkest Knight",
    "Batman: Jekyll & Hyde","Batman: KnightFall","Batman: Legends of the Dark Knight",
    "Batman: Leatherwing","Batman: Mask of the Phantasm","Batman: Master of the Future",
    "Batman: Night Cries","Batman: No Man's Land","Batman: Noel","Batman: Nosferatu",
    "Batman: Odyssey","Batman: Officer Down","Batman: Orphans","Batman: Prey",
    "Batman: Prodigal","Batman: R.I.P.","Batman: Run, Riddler, Run","Batman: Son of the Demon",
    "Batman: Strange Apparitions","Batman: The Abduction","Batman: The Ankh",
    "Batman: The Dark Knight","Batman: The Dark Knight Returns","Batman: The Dark Knight Strikes Again",
    "Batman: The Doom That Came to Gotham","Batman: The Hill","Batman: The Joker's Last Laugh",
    "Batman: The Killing Joke","Batman: The Long Halloween","Batman: The Man Who Laughs",
    "Batman: The Resurrection of Ra's al Ghul","Batman: The Return of Bruce Wayne",
    "Batman: Sword of Azrael","Batman: Two-Face - Crime and Punishment",
    "Batman: Two-Face Strikes Twice","Batman: Under the Hood","Batman: Under the Red Hood",
    "Batman: Vengeance of Bane","Batman: Wayne Family Adventures",
    "Batman: Year One","Batman: Year Two","Batman/Demon","Batman/Green Arrow: The Poison Tomorrow",
    "Batman/Grendel","Batman/Huntress: Cry for Blood","Batman/Joker: The Deadly Duo",
    "Batman/Judge Dredd","Batman/Lobo","Batman/Nightwing: Bloodborne",
    "Batman/Predator","Batman/Ra's al Ghul: Year One","Batman/Scarecrow: Year One",
    "Batman/Spider-Man","Batman/Superman","Batman/Wildcat","Batman/Xenobrood",
    "Batgirl","Batgirl (2nd Series)","Batgirl (3rd Series)","Batgirl: Year One",
    "Batwoman","Batwoman (2nd Series)","Batwing","Big Bang Comics",
    "Birds of Prey","Birds of Prey (2nd Series)","Black Canary","Black Canary (2nd Series)",
    "Black Canary/Oracle: Birds of Prey","Black Hand Comics","Blackhawk","Blackhawk (2nd Series)",
    "Blue Beetle","Blue Beetle (2nd Series)","Blue Beetle (3rd Series)",
    "Blue Devil","Booster Gold","Booster Gold (2nd Series)","Brightest Day",
    "Catwoman (2nd Series)","Catwoman (3rd Series)","Catwoman (4th Series)",
    "Checkmate","Checkmate (2nd Series)","Crisis on Infinite Earths","Cyborg",
    "Damage","Darkstars, The","DC Comics Presents","DC First: Green Lantern/Green Lantern",
    "DC One Million","DC Retroactive","DC Special","DC Super-Stars","DC Universe: Rebirth",
    "DC Universe: The Stories of Alan Moore","Deadshot","Deathstroke (1st Series)",
    "Deathstroke (2nd Series)","Deathstroke: The Terminator","Demon, The","Detective Comics",
    "Doom Patrol (1st Series)","El Diablo","Extreme Justice",
    "Firestorm","Flash, The","Flash, The (2nd Series)","Flash, The (3rd Series)",
    "Flash: The Fastest Man Alive","Forever People, The","Freedom Fighters",
    "Giffen/DeMatteis Justice League","Girl Frenzy","Give Me Liberty",
    "Gotham Central","Gotham City Sirens","Green Arrow","Green Arrow (2nd Series)",
    "Green Arrow (3rd Series)","Green Arrow: The Longbow Hunters","Green Arrow: Year One",
    "Green Lantern","Green Lantern (2nd Series)","Green Lantern (3rd Series)",
    "Green Lantern (4th Series)","Green Lantern: Emerald Dawn","Green Lantern: Emerald Dawn II",
    "Green Lantern: Mosaic","Green Lantern: New Guardians","Green Lantern Corps",
    "Green Lantern Corps (2nd Series)","Guardian, The","Guy Gardner",
    "Hawk and Dove","Hawkman","Hawkman (2nd Series)","Hawkman (3rd Series)",
    "Hawkworld","Hourman","House of Mystery (2nd Series)","House of Secrets (2nd Series)",
    "Identity Crisis","Impulse","Infinite Crisis","JLA",
    "JLA: Act of God","JLA: Age of Wonder","JLA: Classified","JLA: Created Equal",
    "JLA: Earth 2","JLA: Exterminators","JLA: Gatekeeper","JLA: Island of Dr. Moreau",
    "JLA: Riddle of the Beast","JLA: Secret Origins","JLA: Shogun of Steel",
    "JLA: Scary Monsters","JLA: Syndicate Rules","JLA: Tomorrow Woman","JLA/Avengers",
    "JLA/Haven","JLA/Spectre: Soul War","JSA","JSA All Stars","JSA: Strange Adventures",
    "James Robinson's The Golden Age","Jimmy Olsen","Joker","Joker (2nd Series)",
    "Justice","Justice League","Justice League (2nd Series)","Justice League America",
    "Justice League Dark","Justice League Elite","Justice League Europe",
    "Justice League International","Justice League Quarterly","Justice League Task Force",
    "Justice League Unlimited","Justice Society of America","Justice Society of America (2nd Series)",
    "Kingdom Come","Knightfall","Lex Luthor: Man of Steel","Legion of Super-Heroes",
    "Legion of Super-Heroes (2nd Series)","Legion of Super-Heroes (3rd Series)",
    "L.E.G.I.O.N.","Legends","Legends of the DCU","Legends of the DC Universe",
    "Manhunter","Martian Manhunter","Metamorpho","Metal Men","Millenium",
    "Mister Miracle","Mister Terrific","Monarch","Nightwing","Nightwing (2nd Series)",
    "New Gods","New Teen Titans","New Teen Titans (2nd Series)","New Titans",
    "Omega Men","Oracle: The Cure","Our Army at War","Outsiders","Outsiders (2nd Series)",
    "Peacemaker","Phantom Stranger","Plasticman","Plastic Man","Power Girl",
    "Question, The","Question (2nd Series)","Red Tornado","Robin","Robin (2nd Series)",
    "Robin: Year One","Robin 3000","Ronin","Secret Files","Secret Origins",
    "Showcase","Showcase '93","Showcase '94","Showcase '95","Showcase '96",
    "Sgt. Rock","Shadowpact","Shade, The","Shazam!","Sinestro Corps War",
    "Spectre","Spectre (2nd Series)","Spectre (3rd Series)","Starman","Starman (2nd Series)",
    "Stars and S.T.R.I.P.E.","Static","Stormwatch (DC)","Suicide Squad","Suicide Squad (2nd Series)",
    "Superboy","Superboy (2nd Series)","Superboy and the Legion of Super-Heroes",
    "Supergirl","Supergirl (2nd Series)","Supergirl: Wings","Superman",
    "Superman (1st Series)","Superman (2nd Series)","Superman: Birthright",
    "Superman: Blood of My Blood","Superman: Brainiac","Superman: Earth One",
    "Superman: Endgame","Superman: Emperor Joker","Superman: Ending Battle",
    "Superman: For All Seasons","Superman: For Tomorrow","Superman: Gods and Monsters",
    "Superman: Godfall","Superman: Infinite City","Superman: Last Son of Krypton",
    "Superman: New Krypton","Superman: No Limits","Superman: Red Son","Superman: Return to Krypton",
    "Superman: Secret Files","Superman: Secret Identity","Superman: Secret Origin",
    "Superman: The Man of Steel","Superman: The Man of Tomorrow","Superman: True Brit",
    "Superman: Whatever Happened to the Man of Tomorrow?","Superman/Batman",
    "Superman vs. The Amazing Spider-Man","Superman vs. Aliens","Superman/Aliens",
    "Superman: War of the Supermen","Superman: Whatever Happened to the Man of Tomorrow",
    "Swamp Thing (1st Series)","Team Titans","Teen Titans","Teen Titans (2nd Series)",
    "Teen Titans (3rd Series)","Teen Titans Go!","Tempest","Thriller",
    "Timothy Hunter","Titans","Titans (2nd Series)","Tomahawk",
    "Underworld Unleashed","Vigilante","Wanderers","War Games","Weekly World News",
    "Who's Who","Warlord","Wonder Woman","Wonder Woman (1st Series)",
    "Wonder Woman (2nd Series)","Wonder Woman (3rd Series)","Wonder Woman (4th Series)",
    "World's Finest","World's Finest Comics","World Without End","Worlds' Finest (2nd Series)",
    "Xombi","Young Justice","Young Justice (2nd Series)","Young Justice in No Man's Land",
    "Zatanna",
}

DC_KEYWORDS = [
    "batman","superman","green lantern","wonder woman","aquaman","flash, the",
    "justice league","teen titans","lex luthor","gotham","dc comics","booster gold",
    "hawkman","hawkgirl","john constantine","lobo","black canary","deathstroke",
    "nightwing","catwoman","green arrow","metalo","firestorm","hal jordan",
    "swamp thing","martian manhunter","justice society",
]

CHAOS_KEYWORDS = ["lady death","purgatori","chastity","evil ernie","coffin","medieval"]
TOPCOW_KEYWORDS = ["witchblade","magdalena","aphrodite ix"]
DARKNESS_EXACT = {"Darkness, The","Darkness (1st Series), The","Darkness (2nd Series), The",
                  "Darkness (3rd Series), The","Darkness: Spear of Destiny, The",
                  "Darkness/Superman, The","Darkness/Wolverine, The","Darkness/Batman, The",}

AVATAR_EXACT = {
    "303","Apparat Singles Group","Atmospherics (Warren Ellis'...)","Black Summer",
    "Crossed","Crossed (2nd Series)","Crossed: Badlands","Crossed: Wish You Were Here",
    "Doktor Sleepless","Freakangels","Gravel","Ignition City","Planetary (2nd printing)",
    "Rawbone","Scars","Strange Kiss","Strange Killings","Strange Killings: Body Orchard",
    "Strange Killings: Strong Medicine","Strange Killings: The Body Orchard",
    "Supergod","No Hero","Ruins (Avatar)","War Stories (Avatar)",
}

IDW_EXACT = {
    "30 Days of Night","30 Days of Night: 30 Days 'Til Death","30 Days of Night: Dark Days",
    "30 Days of Night: Dead Space","30 Days of Night: Dust to Dust",
    "30 Days of Night: Eben & Stella","30 Days of Night: Red Snow",
    "30 Days of Night: Return to Barrow","30 Days of Night: Spreading the Disease",
    "30 Days of Night: Temptation","Angel","Angel: After the Fall","Angel: Barbary Coast",
    "Angel: Blood & Trenches","Angel: Immortality for Dummies","Angel: Only Human",
    "Angel: Smile Time","Angel: The Curse","Angel: Yearbook","Bloom County: Brand Spanking New Day",
    "Buffy the Vampire Slayer: Season Eight","Buffy the Vampire Slayer: Season Nine",
    "CSI: Crime Scene Investigation","CSI: Dying in the Gutters","CSI: Intern at Your Own Risk",
    "CSI: Miami","CSI: NY","Doctor Who (IDW)","G.I. Joe (IDW)","G.I. Joe: Origins",
    "G.I. Joe: Cobra","Ghost Whisperer","Ghostbusters","Ghostbusters (2nd Series)",
    "Groom Lake","Gula","Haunt of Horror, The: Edgar Allan Poe","Haunted",
    "Locke & Key","Locke & Key: Alpha","Locke & Key: Clockworks","Locke & Key: Crown of Shadows",
    "Locke & Key: Head Games","Locke & Key: Keys to the Kingdom","Locke & Key: Omega",
    "Locke & Key: Small World","Locke & Key: Welcome to Lovecraft",
    "Mars Attacks!","Pandalicious","Rebels (IDW)","Red Tornado (IDW)",
    "Riptide","Star Trek (IDW)","Star Trek: Countdown","Star Trek: Defiant",
    "Star Trek: Deep Space Nine (IDW)","Star Trek: Nero","Star Trek: The Next Generation (IDW)",
    "Star Trek: Voyager (IDW)","Teenage Mutant Ninja Turtles (IDW)",
    "Teenage Mutant Ninja Turtles: The IDW Collection","Transformers (IDW)",
    "Transformers: All Hail Megatron","Transformers: Combiner Wars","Transformers: Dark Cybertron",
    "Transformers: Dark of the Moon","Transformers: Devastation","Transformers: Escalation",
    "Transformers: Infiltration","Transformers: Maximum Dinobots","Transformers: Megatron Origin",
    "Transformers: More Than Meets the Eye","Transformers: Robots in Disguise",
    "Transformers: Stormbringer","Transformers: The IDW Collection","Twitch",
    "True Blood","True Blood: All Together Now","True Blood: Tainted Love","True Blood: The French Quarter",
    "Wormwood: Gentleman Corpse",
}

DYNAMITE_EXACT = {
    "Army of Darkness","Army of Darkness (2nd Series)","Army of Darkness: Ash & the Army of Darkness",
    "Army of Darkness: From the Ashes","Army of Darkness: Home Sweet Hell",
    "Army of Darkness: Hellbillies & Deadites","Army of Darkness: Old School & More",
    "Army of Darkness vs. Re-Animator","Army of Darkness/Xena: Warrior Princess",
    "Battlestar Galactica (Dynamite)","Battlestar Galactica: Ghosts","Battlestar Galactica: Origins",
    "Bionic Man, The","Bionic Woman, The","Buck Rogers","Cassie & Dot",
    "Darkness/Eva: Daughter of Dracula, The","Dracula (Dynamite)","Drive",
    "Evil Ernie (Dynamite)","Evil Ernie: Godeater","Evil Ernie: Revenge",
    "Flash Gordon (Dynamite)","Garth Ennis: Streets of Glory",
    "Girl Comics","Green Hornet (Dynamite)","Green Hornet: Blood Ties",
    "Green Hornet: Golden Age Re-Mastered","Green Hornet: Parallel Lives","Green Hornet: Year One",
    "Groo vs. Conan","Jennifer Blood","John Carter of Mars","Judge Dredd (Dynamite)",
    "Jungle Girl","Jungle Girl Season 2","Jungle Girl Season 3","Lady Death (Dynamite)",
    "Lone Ranger, The","Lone Ranger, The (2nd Series)","Lone Ranger: Vindicated, The",
    "Magnus, Robot Fighter (Dynamite)","Mistress of Death","Mythology: The DC Comics Art of Alex Ross",
    "Necromancer","Pantha","Project Superpowers","Project Superpowers: Chapter 2",
    "Project Superpowers: Blackcross","Project Superpowers: Hero Killers",
    "Purgatori (Dynamite)","Red Sonja","Red Sonja (2nd Series)","Red Sonja vs. Thulsa Doom",
    "Savage Tales","Savage Sword of Conan (Dynamite)","Shadow, The (Dynamite)",
    "Solar: Man of the Atom (Dynamite)","Spark Riders","Sword of Red Sonja: Doom of the Gods",
    "Terminator (Dynamite)","Terminator: Salvation","Turok, Son of Stone (Dynamite)",
    "Vampirella","Vampirella (2nd Series)","Vampirella (3rd Series)","Vampirella Masters Series",
    "Vampirella: Army of Darkness","Vampirella: Bloodlust","Vampirella: Morning in America",
    "Vampirella: Roses for the Dead","Vampirella: Second Coming","Vampirella: The Red Room",
    "Warlord of Mars","Warlord of Mars: Dejah Thoris","Warlord of Mars: Fall of Barsoom",
    "Zorro (Dynamite)","Zorro Rides Again","Zorro: Swords of Hell",
}

IMAGE_EXACT = {
    "27","Acrimony","Alex + Ada","Angelic","Astonishing Wolf-Man, The",
    "Bedlam","Black","Black Science","Birthright","Bitch Planet",
    "Bone (Image)","Brilliant","C.O.W.L.","Chew","Chew: Secret Agent Poyo",
    "Clone","Comeback","Curse","Dangerous","Dead Body Road","Dead Space",
    "Die","Divided States of Hysteria","Dying and the Dead, The",
    "Dynamo 5","East of West","Empty Man, The","Ennio","Enormous",
    "Enigma Force","Fatale","Fear Agent","Five Ghosts","Flintlock",
    "Forge","Friendly Fire","Glitterbomb","God Country","Godland",
    "Graveyard of Empires","Great Pacific","Grim Leaper","Grrl Scouts",
    "Hack/Slash","Hadrian's Wall","Haunt","Head Lopper","Heroes' End",
    "Hip Flask","Hoax Hunters","Hollow Girl","Home","Hometown",
    "Horizon","Huck","Husbands","Invincible","Invincible (1st Series)",
    "Invincible Iron Man","Island","It Girl! and the Atomics","I Hate Fairyland",
    "Kick-Ass","Kick-Ass 2","Kick-Ass 3","Killadelphia","Kill or be Killed",
    "King: The Phantom","Letter 44","Low","Lazarus","Maestros",
    "Manhattan Projects, The","Manifest Destiny","Monstress","Moon Knight (Image)",
    "Morning Glories","Nowhere Men","Nocturnals: Black Planet, The","No Mercy",
    "Outcast","Outer Darkness","Pax Americana","Paper Girls","Phonogram",
    "Planetoid","Pleece & Pleece","Plot, The","Pretty Deadly","Prophet",
    "Redneck","Revival","Rocket Girl","Rot & Ruin","Rumble",
    "Saga","Savage Dragon","Savage Dragon (1st Series)","Savage Dragon (2nd Series)",
    "Savage Dragon (3rd Series)","Sex","Sex Criminals","Sheltered","Shutter",
    "Sideways","Silver","Sit Down, Shut Up","Skull Kickers","Skybound Presents",
    "Sleeping Giants","Sonata","Space Bandits","Spawn","Spawn (1st Series)",
    "Spawn (2nd Series)","Stray Bullets","Stray Bullets: Sunshine & Roses",
    "Stronghold","Supermansion","Think Tank","Tokyo Ghost","Trees",
    "Ultra","Uncanny","Unit 44","Upgrade Soul","Violent","Visible Man, The",
    "Warhammer: Condemned","Wayward","Weatherman, The","We Stand on Guard",
    "Wytches","X-Men/Gen 13","Xena: Warrior Princess (Image)","Zero Killer",
}

IMAGE_KEYWORDS = [
    "spawn","savage dragon","witchblade","cyberforce","gen 13","wildcats",
    "stormwatch (image)","wetworks","divine right","union (image)",
    "danger girl","leave it to chance","lazarus","saga","walking dead",
    "invincible","east of west","black science","sex criminals","deadly class",
    "paper girls","pretty deadly","velvet","southern bastards","trees",
]

DARK_HORSE_KEYWORDS = [
    "hellboy","b.p.r.d.","sin city","abe sapien","lobster johnson",
    "mignolaverse","dark horse","goon, the","conan (dark horse)",
    "buffy (dark horse)","star wars (dark horse)","usagi yojimbo",
]

DARK_HORSE_EXACT = {
    "9-11","Aliens","Aliens vs. Predator","American Gods",
    "Arzach","Black Hammer","Brain Boy","Catalyst Comix",
    "Comics' Greatest World","Comics' Greatest World: Arcadia",
    "Comics' Greatest World: Golden City","Comics' Greatest World: Steel Harbor",
    "Comics' Greatest World: Vortex","Comics' Greatest World: X",
    "Concrete","Eerie","Eisner","Groo (Dark Horse)","Grendel",
    "Grendel: Black, White & Red","Grendel: Behold the Devil",
    "Ghost","Ghost (2nd Series)","Ghost/Batgirl","Ghost/Hellboy",
    "Herbie","The Mask","Madman","Madman Comics",
    "Mask, The","Magnus, Robot Fighter (Dark Horse)","Martha Washington",
    "Next Nexus","Next Men","Nexus (Dark Horse)","Predator","Predator (2nd Series)",
    "Predator vs. Magnus, Robot Fighter","Randy O'Donnell Is The Man",
    "Robocop","Robocop (2nd Series)","Robocop (3rd Series)",
    "Robocop: Mortal Coils","Robocop: Prime Suspect","Robocop: Roulette",
    "Robocop: Wild Child","Robocop 2","Sin City: A Dame to Kill For",
    "Star Wars: Crimson Empire","Star Wars: Dark Empire","Star Wars: Dark Empire II",
    "Star Wars: Dark Forces - Rebel Agent","Star Wars: Empire",
    "Star Wars: Knights of the Old Republic",
    "Star Wars: Legacy","Star Wars: Rebellion","Star Wars: Republic",
    "Star Wars: Union","Star Wars: X-Wing Rogue Squadron",
    "The Mask: Hunt for the Green Lantern","The Mask Returns",
    "The Mask: Official Movie Adaptation","The Mask: Strikes Back",
    "The Mask: Southern Discomfort","The Mask: Virtual Surreality",
    "The Mask: World Tour","The Mask: Zero","The Mask (2nd Series)",
    "X","X (2nd Series)",
}

WILDSTORM_EXACT = {
    "Astro City/Arrowsmith","Authority, The","Authority (2nd Series), The",
    "Brutes & Babes","Captain Atom: Armageddon","Divine Right",
    "Eye of the Storm","Eye of the Storm Annual","Fathom (WildStorm)",
    "Gen 13","Gen 13 (1st Series)","Gen 13 (2nd Series)","Gen 13 (3rd Series)",
    "Gen 13 (4th Series)","Gen 13: A Christmas Caper","Gen 13: Ordinary Heroes",
    "H.A.R.D. Corps","Midnighter","Midnighter (2nd Series)","Midnighter: Apollo",
    "Number of the Beast","Number of the Beast: The Counting",
    "Planetary","Planetary (1st Series)","Planetary/Authority: Ruling the World",
    "Planetary/Batman: Night on Earth","Planetary/JLA: Terra Occulta",
    "Planetary/The Authority: Ruling the World",
    "Sleeper","Sleeper: Season Two","Stormwatch","Stormwatch: Team Achilles",
    "Stormwatch: P.H.D.","Stormwatch Post Human Division",
    "Tom Strong","Tom Strong (2nd Series)","Tom Strong's Terrific Tales",
    "Terra Obscura","Terra Obscura (2nd Series)",
    "Wetworks","Wetworks (2nd Series)","WildC.A.T.S","WildC.A.T.s",
    "WildC.A.T.s (1st Series)","WildC.A.T.s (2nd Series)","WildC.A.T.s (3rd Series)",
    "WildCATS (Version 3.0)","WildStorm Presents","WildStorm Rising","WildStorm Summer Special",
    "WildStorm Universe","Wildcats: Covert Action Teams","Wildcats Version 3.0",
    "Wildcats: World's End",
}

VALIANT_EXACT = {
    "Archer & Armstrong","Bloodshot","Bloodshot (2nd Series)","Bloodshot and H.A.R.D. Corps",
    "Eternal Warrior","Eternal Warrior (2nd Series)","H.A.R.D. Corps",
    "Harbinger","Harbinger (2nd Series)","Harbinger Wars",
    "Ivar, Timewalker","Livewire","Ninjak","Ninjak (2nd Series)",
    "Quantum and Woody","Quantum and Woody (2nd Series)","Rai",
    "Secret Weapons","Shadowman","Shadowman (2nd Series)","Solar, Man of the Atom",
    "Timewalker","Toyo Harada","Unity","Unity (2nd Series)","X-O Manowar",
    "X-O Manowar (2nd Series)","X-O Manowar (3rd Series)",
}

MARVEL_PATTERNS = [
    "spider-man","spiderman","x-men","x-force","x-factor","x-statix","x-treme",
    "avengers","iron man","captain america","thor","hulk","fantastic four",
    "daredevil","wolverine","deadpool","punisher","ghost rider","black panther",
    "guardians of the galaxy","nova","silver surfer","doctor strange",
    "nick fury","shield","s.h.i.e.l.d","luke cage","power man","iron fist",
    "hawkeye","black widow","scarlet witch","vision","ant-man","wasp",
    "she-hulk","namor","doctor doom","galactus","thanos","venom","carnage",
    "elektra","moon knight","ms. marvel","captain marvel","war machine",
    "mister fantastic","invisible woman","human torch","thing, the",
    "colossus","cyclops","magneto","professor x","jean grey","storm",
    "gambit","rogue","jubilee","beast","iceman","nightcrawler",
    "psylocke","archangel","bishop","cable","cannonball","sunspot",
    "siryn","multiple man","strong guy","madrox","polaris",
    "excalibur","new mutants","generation x","academy x",
    "heroes for hire","secret avengers","mighty avengers","dark avengers",
    "young avengers","west coast avengers","force works",
    "alpha flight","omega flight","squadron supreme","exiles",
    "new warriors","thunderbolts","dark reign","siege","fear itself",
    "acts of vengeance","civil war","secret invasion","house of m",
    "annihilation","annihilators","war of kings","realm of kings",
    "planet hulk","world war hulk","world war hulks",
    "mutant x","mutation nation","morlock","morlocks",
    "marvel","marvel comics","epic comics","marvel limited",
    "marvel fanfare","marvel select","marvel saga","marvel tales",
    "marvel feature","marvel premiere","marvel spotlight","marvel super heroes",
    "marvel team-up","marvel two-in-one","marvel universe",
    "what if?","what if","marvel age","marvel adventures",
    "official handbook of the marvel universe","ohotmu",
    "peter parker","mary jane","miles morales",
    "sentry, the","sentry","quasar","thunderstrike","darkhawk",
    "machine man","sleepwalker","darkhawk","speedball","silhouette",
    "rage","proportioned","proportional","spider-girl","spider-woman",
    "spider-man 2099","2099","2099 a.d.","2099 unlimited",
    "onslaught","operation: zero tolerance","maximum security",
    "phalanx covenant","age of apocalypse","apocalypse",
    "decimation","messiah complex","second coming","schism",
    "avengers vs. x-men","avx","inhumans","medusa","black bolt","crystal",
    "eternals","celestials","infinity gauntlet","infinity war",
    "infinity crusade","infinity watch","warlock","adam warlock",
    "kree","skrull","shi'ar","technet","brood",
    "starjammers","imperial guard","deathbird","lilandra",
    "shatterstar","longshot","dazzler","havok","polaris",
    "marvel monsters","marvel horror","tomb of dracula",
    "frankenstein","werewolf by night","son of satan","morbius",
    "legion of monsters","monster of frankenstein",
    "power pack","cloak and dagger","new warriors",
    "american dream","a-next","j2","next avengers",
    "captain britain","captain universe","captain marvel",
    "firestar","feral","catseye","boom boom","rictor","wolfsbane",
    "domino","forge","warpath","thunderbird","mirage",
    "marvel knights","marvel max","icon comics (marvel)",
]

MARVEL_EXACT = {
    "5 Ronin","Alias","Amazing Fantasy","Amazing Adventures","Amazing Adult Fantasy",
    "Amazing Spider-Man, The","Amazing Spider-Man Annual, The",
    "Amazing X-Men","Avenging Spider-Man","Avengers, The",
    "Avengers Academy","Avengers Assemble","Avengers Arena",
    "Avengers Forever","Avengers Infinity","Avengers: The Children's Crusade",
    "Avengers: The Initiative","Avengers vs. X-Men","Avengers vs. X-Men: Consequences",
    "Avengers: X-Sanction","Avengers/Invaders",
    "Black Panther (1st Series)","Black Panther (2nd Series)","Black Panther (3rd Series)",
    "Black Panther (4th Series)","Black Panther (5th Series)","Black Panther (6th Series)",
    "Cable","Cable (2nd Series)","Cable & Deadpool","Cable & X-Force","Cable: Blood & Metal",
    "Classic X-Men","Dark X-Men","Deadpool","Deadpool (2nd Series)","Deadpool (3rd Series)",
    "Deadpool Corps","Deadpool MAX","Deadpool Merc with a Mouth","Deadpool: Merc with a Mouth",
    "Deadpool Team-Up","Deadpool vs. X-Force","Deadpool: Back in Black",
    "Deathlok","Deathlok (2nd Series)","Defenders","Defenders (2nd Series)","Defenders (3rd Series)",
    "Fallen Son: The Death of Captain America","First X-Men","Formic Wars",
    "Generation Hope","Generation X","Giant-Size X-Men","Infinity Gauntlet, The",
    "Infinity Gauntlet","Infinity War","Infinity Crusade","Incredible Hulk, The",
    "Incredible Hulk (1st Series)","Incredible Hulk (2nd Series)",
    "Invincible Iron Man","Iron Man","Iron Man (1st Series)","Iron Man (2nd Series)",
    "Iron Man (3rd Series)","Iron Man (4th Series)","Iron Man (5th Series)",
    "Iron Man 2020","Iron Man Annual","Marvels","Marvels (2nd Series)",
    "Marvels: Eye of the Camera","Marvel 1602","Marvel Age","Marvel Chillers",
    "Marvel Comics Presents","Marvel Holiday Special","Marvel Masterworks",
    "Marvel Milestone Edition","Marvel Must Haves","Marvel Preview",
    "New Avengers","New Avengers (2nd Series)","New Avengers: Illuminati",
    "New Excalibur","New X-Men","New X-Men (2nd Series)","New X-Men: Academy X",
    "Onslaught: Marvel Universe","Onslaught: X-Men","Onslaught Unleashed",
    "Origin","Origin II","Original Sin","Runaways","Runaways (2nd Series)",
    "Secret Warriors","Skaar: Son of Hulk","Spider-Island","Spider-Men",
    "Superior Spider-Man","Superior Spider-Man Team Up","Superior Foes of Spider-Man, The",
    "Swamp Thing (Marvel)","Thor","Thor (1st Series)","Thor (2nd Series)","Thor (3rd Series)",
    "Thor Annual","Thor Corps","Thor: Ages of Thunder","Thor: For Asgard",
    "Thor: God of Thunder","Thor: Heaven & Earth","Thor: The Deviants Saga",
    "Thor: The Trial of Thor","Thor: Vikings","Thor: Wolves of the North",
    "Thunderbolts","Thunderbolts (2nd Series)","Thunderbolts: From the Marvel Vault",
    "Ultimate Avengers","Ultimate Captain America","Ultimate Comics Avengers",
    "Ultimate Comics Avengers vs. New Ultimates","Ultimate Comics Spider-Man",
    "Ultimate Comics X-Men","Ultimate Doomsday","Ultimate Extinction",
    "Ultimate Fantastic Four","Ultimate Human","Ultimate Mystery",
    "Ultimate Origins","Ultimate Power","Ultimate Secrets","Ultimate Six",
    "Ultimate Spider-Man","Ultimate Spider-Man Special","Ultimate Vision",
    "Ultimate War","Ultimate X-Men","Ultimate X-Men (2nd Series)","Ultimates, The",
    "Ultimates 2, The","Ultimates 3, The","Ultimatum","Uncanny Avengers",
    "Uncanny X-Force","Uncanny X-Men","Uncanny X-Men (1st Series)",
    "Uncanny X-Men (2nd Series)","Uncanny X-Men Annual","Uncanny X-Men: First Class",
    "Wolverine","Wolverine (1st Series)","Wolverine (2nd Series)","Wolverine (3rd Series)",
    "Wolverine (4th Series)","Wolverine Annual","Wolverine First Class",
    "Wolverine: Best There Is, The","Wolverine: Black Rio","Wolverine: Bloodlust",
    "Wolverine: Dark Mirror","Wolverine: Days of Future Past",
    "Wolverine: Evolution","Wolverine: Exit Wounds","Wolverine: First Class",
    "Wolverine: Flies to a Spider","Wolverine: Hunting Season","Wolverine: Japan's Most Wanted",
    "Wolverine: Killing Made Simple","Wolverine: Manifest Destiny",
    "Wolverine: Old Man Logan","Wolverine: Origins","Wolverine: Rot",
    "Wolverine: Savage","Wolverine: Saudade","Wolverine: Soultaker",
    "Wolverine: The Best There Is","Wolverine: Weapon X","Wolverine/Cable",
    "Wolverine/Deadpool","Wolverine/Gambit","Wolverine/Hulk","Wolverine/Nick Fury",
    "Wolverine/Punisher","Wolverine/Punisher Revelation",
    "X-Factor","X-Factor (1st Series)","X-Factor (2nd Series)","X-Factor (3rd Series)",
    "X-Force","X-Force (1st Series)","X-Force (2nd Series)","X-Force (3rd Series)",
    "X-Force Annual","X-Force/Cable","X-Force/Champions","X-Force/Deadpool",
    "X-Men","X-Men (1st Series)","X-Men (2nd Series)","X-Men (3rd Series)",
    "X-Men Adventures","X-Men Alpha","X-Men Annual","X-Men Archives",
    "X-Men Vs. Avengers","X-Men: Age of Apocalypse","X-Men: Endangered Species",
    "X-Men: Earth's Mutant Heroes","X-Men: Evolution","X-Men: First Class",
    "X-Men: First Class (2nd Series)","X-Men: First Class Finals",
    "X-Men: Forever","X-Men: Forever (2nd Series)","X-Men: God Loves, Man Kills",
    "X-Men: Gold","X-Men: Grand Design","X-Men: Hidden Years",
    "X-Men: Kitty Pryde - Shadow & Flame","X-Men: Legacy","X-Men: Magneto Testament",
    "X-Men: Manifest Destiny","X-Men: Messiah Complex","X-Men: Negative Zone",
    "X-Men: No More Humans","X-Men: Noir","X-Men: Odd Men Out",
    "X-Men: Phoenix - Endsong","X-Men: Phoenix - Warsong","X-Men: Phoenix Force Handbook",
    "X-Men: Pixie Strikes Back","X-Men: Prelude to Schism","X-Men: Prisoner X",
    "X-Men: Rarities","X-Men: Red","X-Men: Reload","X-Men: Ronin",
    "X-Men: Search for Cyclops","X-Men: Smoke and Blood","X-Men: The 198 Files",
    "X-Men: The Complete Age of Apocalypse Epic","X-Men: The End",
    "X-Men: The Magneto War","X-Men: True Friends","X-Men: Unlimited",
    "X-Men: Wrath of Apocalypse","X-Men/Alpha Flight","X-Men/Brood",
    "X-Men/ClanDestine","X-Men/Fantastic Four","X-Men/Magneto: Wild Children",
    "X-Men/Spider-Man","X-Men 2099","X-Statix","X-Statix Presents: Dead Girl",
    "X-Treme X-Men","X-Treme X-Men: Savage Land",
}

MARVEL_MAX_EXACT = {
    "Black Panther: The Most Dangerous Man Alive","Foolkiller","Fury MAX",
    "Fury: My War Gone By","Garth Ennis: The Fury","Haunt of Horror, The",
    "Howard the Duck MAX","Hulk: Season One",
    "Incredible Hulk MAX","MAX: Comics for Adults","Max","MAX: A Marvel Comics Limited Series",
    "Men of War","Nick Fury's Howling Commandos","Punisher MAX",
    "Punisher MAX: Get Castle","Punisher MAX: Tiny Ugly World",
    "Punisher: The Tyger","Punisher: The Platoon","Punisher: Red X-Mas",
    "Punisher: Frank Castle MAX","Punisher: War is Hell","Punisher: MAX",
    "Strange Tales: Dark Corners","Wolverine MAX",
}

MARVEL_MAX_KEYWORDS = ["punisher max","fury max","wolverine max","max: a marvel","hulk max"]

ICON_MARVEL_EXACT = {
    "Criminal","Criminal (2nd Series)","Criminal: The Sinners",
    "Criminal: The Last of the Innocent","Criminal: Wrong Time Wrong Place",
    "Incognito","Incognito: Bad Influences","Powers","Powers (2nd Series)",
    "Powers: Bureau","Powers: The Definitive Hardcover Collection",
    "Scarlet","Scarlet (2nd Series)","United States vs. Murder, Inc.",
}

MANGA_KEYWORDS = [
    "viz","manga","shonen","shojo","seinen","tokyopop","vertical inc",
    "dragon ball","naruto","one piece","bleach","death note","fullmetal alchemist",
    "sailor moon","akira","ghost in the shell","evangelion",
    "berserk","vagabond","vinland saga","monster (manga)",
    "ranma","inuyasha","rurouni kenshin",
]

GOLDEN_AGE = {
    "4Most": "Novelty Press",
    "3-D Exotic Beauties": "3-D Zone/Blackthorne",
}

OTHER_EXACT = {
    # Oni Press
    "Local": "Oni Press","Scott Pilgrim": "Oni Press","Scott Pilgrim vs. the World": "Oni Press",
    "Scott Pilgrim & the Infinite Sadness": "Oni Press",
    "Scott Pilgrim Gets It Together": "Oni Press","Scott Pilgrim's Precious Little Life": "Oni Press",
    "Scott Pilgrim's Finest Hour": "Oni Press",
    "Stumptown": "Oni Press","Stumptown (2nd Series)": "Oni Press",
    "Queen & Country": "Oni Press","Queen & Country: Declassified": "Oni Press",
    "Wasteland (Oni)": "Oni Press","Whiteout": "Oni Press","Whiteout: Melt": "Oni Press",
    # Fantagraphics
    "Love and Rockets": "Fantagraphics","Love and Rockets (2nd Series)": "Fantagraphics",
    "Love and Rockets: New Stories": "Fantagraphics",
    "Eightball": "Fantagraphics","Ghost World": "Fantagraphics",
    "Peanuts (Fantagraphics)": "Fantagraphics",
    "Complete Chester Gould's Dick Tracy, The": "Fantagraphics",
    "Complete Peanuts, The": "Fantagraphics",
    # Abstract Studio
    "Strangers in Paradise": "Abstract Studio","Strangers in Paradise (2nd Series)": "Abstract Studio",
    "Strangers in Paradise (3rd Series)": "Abstract Studio","Echo": "Abstract Studio",
    # Mirage
    "Teenage Mutant Ninja Turtles (Mirage)": "Mirage Studios",
    "TMNT: Teenage Mutant Ninja Turtles": "Mirage Studios",
    # Archie
    "Archie": "Archie Comics","Archie (2nd Series)": "Archie Comics",
    "Archie Comics": "Archie Comics","Archie Double Digest": "Archie Comics",
    "Betty and Veronica": "Archie Comics","Jughead": "Archie Comics",
    # Drawn & Quarterly
    "Palomar: The Heartbreak Soup Stories": "Drawn & Quarterly",
    # CrossGen
    "Sigil": "CrossGen Comics","Scion": "CrossGen Comics",
    "Mystic": "CrossGen Comics","Sojourn": "CrossGen Comics",
}

# ─────────────────────────────────────────────
# Classification function
# ─────────────────────────────────────────────

def assign_publisher(t: str) -> str:
    tl = t.lower()

    # Exact overrides first
    if t in GOLDEN_AGE:
        return GOLDEN_AGE[t]
    if t in OTHER_EXACT:
        return OTHER_EXACT[t]

    # Top Cow
    if t in DARKNESS_EXACT:
        return "Top Cow Productions"
    if any(x in tl for x in TOPCOW_KEYWORDS):
        return "Top Cow Productions"

    # Chaos! / Dynamite
    if any(x in tl for x in CHAOS_KEYWORDS):
        if "(dynamite)" in tl:
            return "Dynamite Entertainment"
        if "(boundless)" in tl:
            return "Boundless Comics"
        return "Chaos! Comics"

    # Avatar Press
    if t in AVATAR_EXACT:
        return "Avatar Press"

    # Vertigo
    if t in VERTIGO:
        return "DC/Vertigo"

    # DC exact
    if t in DC_EXACT:
        return "DC Comics"
    if any(x in tl for x in DC_KEYWORDS):
        return "DC Comics"

    # IDW
    if t in IDW_EXACT:
        return "IDW Publishing"

    # Dynamite
    if t in DYNAMITE_EXACT:
        return "Dynamite Entertainment"

    # Image exact
    if t in IMAGE_EXACT:
        return "Image Comics"
    if any(x in tl for x in IMAGE_KEYWORDS):
        return "Image Comics"

    # Dark Horse
    if t in DARK_HORSE_EXACT:
        return "Dark Horse Comics"
    if any(x in tl for x in DARK_HORSE_KEYWORDS):
        return "Dark Horse Comics"

    # WildStorm
    if t in WILDSTORM_EXACT:
        return "WildStorm"

    # Valiant
    if t in VALIANT_EXACT:
        return "Valiant Comics"

    # Manga
    if any(x in tl for x in MANGA_KEYWORDS):
        return "Manga Publisher"

    # Marvel MAX
    if t in MARVEL_MAX_EXACT:
        return "Marvel MAX"
    if any(x in tl for x in MARVEL_MAX_KEYWORDS):
        return "Marvel MAX"

    # Icon (Marvel)
    if t in ICON_MARVEL_EXACT:
        return "Icon (Marvel)"

    # Marvel catch-all
    if t in MARVEL_EXACT:
        return "Marvel Comics"
    for pat in MARVEL_PATTERNS:
        if pat in tl:
            return "Marvel Comics"

    return "Unknown/Independent"


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    use_existing_map = "--from-map" in sys.argv and MAP_FILE.exists()

    # Load titles
    with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from {DATA_FILE.name}")

    # Build publisher map
    if use_existing_map:
        with open(MAP_FILE, 'r') as f:
            pub_map = json.load(f)
        print(f"Loaded existing map with {len(pub_map)} entries (--from-map mode)")
    else:
        unique_titles = sorted({r['Title'] for r in rows})
        print(f"Classifying {len(unique_titles)} unique titles...")
        pub_map = {t: assign_publisher(t) for t in unique_titles}

    # Save map
    with open(MAP_FILE, 'w') as f:
        json.dump(pub_map, f, indent=2, sort_keys=True)
    print(f"Publisher map saved to {MAP_FILE.name}")

    # Stats
    counts = Counter(pub_map.values())
    print("\n=== Publisher distribution ===")
    for pub, count in counts.most_common():
        print(f"  {pub:<45} {count:>5}")

    unknowns = sorted(t for t, p in pub_map.items() if p == 'Unknown/Independent')
    with open(UNKNOWN_FILE, 'w') as f:
        f.write(f"Unknown/Independent titles: {len(unknowns)}\n\n")
        for t in unknowns:
            f.write(t + "\n")
    print(f"\nUnknown titles ({len(unknowns)}) written to {UNKNOWN_FILE.name}")

    # Check if Publisher column exists
    if 'Publisher' not in fieldnames:
        new_fieldnames = [fieldnames[0], 'Publisher'] + fieldnames[1:]
    else:
        new_fieldnames = fieldnames

    # Write updated file
    backup = DATA_FILE.parent / (DATA_FILE.stem + "_BACKUP.txt")
    if not backup.exists():
        shutil.copy2(DATA_FILE, backup)
        print(f"Backup created: {backup.name}")

    with open(DATA_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            row['Publisher'] = pub_map.get(row['Title'], 'Unknown/Independent')
            writer.writerow(row)

    print(f"\nFile updated: {DATA_FILE.name} ({len(rows)} rows written)")
    print("Done.")


if __name__ == '__main__':
    main()
