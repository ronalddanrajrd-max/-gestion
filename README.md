# 🤖 Bot Discord Complet — Python

Un bot Discord complet avec modération, tickets, giveaways, musique, logs et plus encore.

---

## 📁 Structure des fichiers

```
bot_discord/
├── main.py                 # Point d'entrée
├── requirements.txt        # Dépendances
├── .env.example            # Template de configuration
├── data/                   # Données (créé automatiquement)
│   ├── config.json         # Configuration par serveur
│   ├── warns.json          # Avertissements
│   ├── tickets.json        # Tickets ouverts
│   └── giveaways.json      # Giveaways actifs
└── cogs/
    ├── moderation.py       # Commandes de modération
    ├── roles.py            # Gestion des rôles
    ├── welcome.py          # Bienvenue / départ
    ├── tickets.py          # Système de tickets
    ├── giveaway.py         # Giveaways & sondages
    ├── stats.py            # Statistiques
    ├── logs.py             # Logs automatiques
    ├── fun.py              # Commandes fun
    ├── music.py            # Musique YouTube
    └── config.py           # Configuration & aide
```

---

## 🚀 Installation

### 1. Pré-requis
- Python 3.10 ou supérieur
- FFmpeg installé sur le système (pour la musique)

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer le token
Copie `.env.example` en `.env` et remplace le token :
```bash
cp .env.example .env
```
Modifie `.env` :
```
DISCORD_TOKEN=ton_vrai_token_discord
```

### 4. Obtenir un token Discord
1. Va sur https://discord.com/developers/applications
2. Crée une application → "Bot" → "Reset Token"
3. Active **tous les Intents** (Presence, Server Members, Message Content)
4. Invite le bot avec les permissions : `Administrator`

### 5. Lancer le bot
```bash
python main.py
```

---

## 📋 Commandes disponibles

### 🛡️ Modération
| Commande | Description | Permission requise |
|---|---|---|
| `/ban @user [raison]` | Bannir un membre | Ban Members |
| `/kick @user [raison]` | Expulser un membre | Kick Members |
| `/mute @user [durée] [raison]` | Timeout un membre | Moderate Members |
| `/unmute @user` | Enlever le mute | Moderate Members |
| `/warn @user [raison]` | Avertir un membre | Manage Messages |
| `/warns @user` | Voir les warns | Manage Messages |
| `/clearwarn @user` | Effacer les warns | Administrator |
| `/purge [nombre]` | Supprimer des messages | Manage Messages |
| `/lock` | Verrouiller le salon | Manage Channels |
| `/unlock` | Déverrouiller le salon | Manage Channels |
| `/slowmode [secondes]` | Mode lent | Manage Channels |
| `/unban [user_id]` | Débannir | Ban Members |

### 🎭 Rôles
| Commande | Description |
|---|---|
| `/role-add @user @role` | Ajouter un rôle |
| `/role-remove @user @role` | Retirer un rôle |
| `/autorole @role` | Rôle automatique à l'arrivée |
| `/reactionrole @role emoji [texte]` | Rôle par réaction |

### 👋 Bienvenue & Départ
| Commande | Description |
|---|---|
| `/setwelcome #salon [message]` | Configurer la bienvenue |
| `/setleave #salon [message]` | Configurer le départ |

Variables disponibles dans les messages : `{member}`, `{server}`

### 🎫 Tickets
| Commande | Description |
|---|---|
| `/ticket-setup #salon [catégorie]` | Envoyer le panel de tickets |

Le panel affiche un bouton. Les membres cliquent pour ouvrir un ticket privé.

### 🎉 Giveaways & Sondages
| Commande | Description |
|---|---|
| `/giveaway-start [durée] [gagnants] [prix]` | Lancer un giveaway |
| `/giveaway-reroll [message_id]` | Retirer un gagnant |
| `/poll [question]` | Créer un sondage |
| `/suggest [idée]` | Envoyer une suggestion |

### 📊 Statistiques
| Commande | Description |
|---|---|
| `/userinfo [@user]` | Infos sur un membre |
| `/serverinfo` | Infos sur le serveur |
| `/botinfo` | Infos sur le bot |
| `/ping` | Latence du bot |
| `/avatar [@user]` | Voir un avatar |

### 🎵 Musique
| Commande | Description |
|---|---|
| `/play [titre/url]` | Jouer une musique |
| `/skip` | Passer la piste |
| `/queue` | Voir la file d'attente |
| `/stop` | Arrêter et déconnecter |
| `/pause` | Mettre en pause |
| `/resume` | Reprendre |

> ⚠️ Nécessite **FFmpeg** installé sur le système.
> Sur Ubuntu/Debian : `sudo apt install ffmpeg`
> Sur Windows : Télécharge ffmpeg.org et ajoute au PATH.

### 🎮 Fun
| Commande | Description |
|---|---|
| `/8ball [question]` | Boule magique |
| `/coinflip` | Pile ou face |
| `/dice [faces]` | Lancer un dé |
| `/choose [options]` | Choisir parmi des options |
| `/joke` | Blague aléatoire |
| `/rps` | Pierre, feuille, ciseaux |

### ⚙️ Configuration
| Commande | Description |
|---|---|
| `/setup` | Affiche les commandes de config |
| `/setlogs #salon` | Définir le salon de logs |
| `/setsuggest #salon` | Salon de suggestions |
| `/help` | Liste toutes les commandes |

---

## 📝 Logs automatiques

Une fois `/setlogs` configuré, le bot logue automatiquement :
- Messages supprimés
- Messages modifiés
- Arrivées et départs de membres
- Bans et unbans
- Changements de rôles

---

## ❓ Problèmes courants

**Le bot ne répond pas aux slash commands ?**
→ Attends jusqu'à 1 heure que Discord synchronise les commandes. Ou rejoins le bot à un seul serveur de test et sync manuellement.

**Erreur FFmpeg pour la musique ?**
→ Installe FFmpeg et assure-toi qu'il est dans le PATH système.

**Les intents ne fonctionnent pas ?**
→ Active TOUS les intents dans le portail développeur Discord pour ton bot.
