#Import libraries
import pandas as pd
import os
from src.components.sessionsimulator import BlacjackCareerSim
from config import config_variables

# Read basic strategy
global_path = os.getcwd()
src_folder = "src"
data_folder = "data"
filename = "Blackjack_BSE.xlsx"

#Import basic strategy df
path_to_bse = os.path.join(global_path, src_folder, data_folder, filename)
bse_df = pd.read_excel(path_to_bse, sheet_name=None)


#Run sim
blackjack_sim = BlacjackCareerSim(bse_df, config_variables)
blackjack_sim.blackjack_sim()
