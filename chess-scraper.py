import pandas as pd
import datetime
import time
import hashlib
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

now = datetime.datetime.now()

USERNAME = "your_chess_com_login"
PASSWORD = "your_chess_com_password"
GAMES_URL = "https://www.chess.com/games/archive?gameOwner=other_game&username=" + \
	USERNAME + \
	"&gameType=live&gameResult=&opponent=&opening=&color=&gameTourTeam=&" + \
	"timeSort=desc&rated=rated&startDate%5Bdate%5D=08%2F01%2F2013&endDate%5Bdate%5D=" + \
	str(now.month) + "%2F" + str(now.day) + "%2F" + str(now.year) + \
	"&ratingFrom=&ratingTo=&page="
LOGIN_URL = "https://www.chess.com/login"

# l'executable doit se trouver à coté du script python 
# (dans le meme repertoire)
driver = webdriver.Chrome("chromedriver.exe", options=options)
# il faut désactiver le javascript manuellement avant 
# que le scrapping démarre
driver.get("chrome://settings/content/javascript")
time.sleep(5)
driver.get(LOGIN_URL)
driver.find_element_by_id("username").send_keys(USERNAME)
driver.find_element_by_id("password").send_keys(PASSWORD)
driver.find_element_by_id("login").click()
time.sleep(5)

tables = []
game_links = []
countries_w = []
countries_b = []
# 35 corresponds au nombre de page que j'ai
# il y'a au maximum 50 parties par page
for page_number in range(35):
	driver.get(GAMES_URL + str(page_number + 1))
	time.sleep(5)
	# dfs est un tableau d'une case avec le contenu d'une page soit 50 parties maximum
	dfs = pd.read_html(driver.page_source, attrs={'class':'table-component table-hover archive-games-table'})
	tables.append(dfs[0])
	table_user_cells = driver.find_elements_by_class_name('archive-games-user-cell')
	for cell in table_user_cells:
		link = cell.find_elements_by_tag_name('a')[0]
		game_links.append(link.get_attribute('href'))
		flags = cell.find_elements_by_css_selector('div.user-tagline-component div')
		# au 23/04/2022 les drapeau russes et bielorusse ne sont plus affichés
		# sur le site chess com; De ce fait, si le tableau ramene
		# moins de 2 drapeaux, alors, les deux sont passés à Unknown
		flag_w = "'Unknown'"
		flag_b = "'Unknown'"
		if len(flags) == 2 :
			flag_w = flags[0].get_attribute('v-tooltip')
			flag_b = flags[1].get_attribute('v-tooltip')
		countries_w.append(flag_w)
		countries_b.append(flag_b)

driver.close()
# games est la concatenation de toutes les pages
games = pd.concat(tables)

# reset de l'index pour que les liens entre
# games, link, et countries puissent se faire
# de base ça va de 0 à 49 puis ça repart à zero
games = games.reset_index()

print('games :')
print(games)
# creation d'un identifiant unique hashé pour la partie
identifier = pd.Series(
	games['Joueurs'] + str(games['Résultat']) + str(games['Coups']) + games['Date']
).apply(lambda x: x.replace(" ", ""))

games.insert(
	0, 
	'GameId', 
	identifier.apply(lambda x: hashlib.sha1(x.encode("utf-8")).hexdigest())
)
games['Link'] = pd.Series(game_links)
games['Countries_w'] = pd.Series(countries_w)
games['Countries_b'] = pd.Series(countries_b)
# Le CSV en sortie est exploité dans PowerBI
games.to_csv("games_results.csv")