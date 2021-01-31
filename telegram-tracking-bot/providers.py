# Module imports
import requests
import logging as log
from datetime import datetime
import pytz

class Providers():
    """
    This class groups all of the functions to get data from 
    tracking companies.
    """
    def __init__(self):
        self.supported = ["oca"]
        self.real_names = ["Oca"]

        # Define timeout
        self.timeout = 10   # in seconds
        self.timezone = pytz.timezone("America/Argentina/Buenos_Aires")
        
    def get(self, tracknum, company):
        """
        Points to the different get functions according
        to the given company. If company not supported, returns None.
        """
        if company == "oca":
            return(self._get_oca(tracknum))
        else:
            return None

    def _get_oca(self, tracknum: str) -> list:
        """
        Gets tracking data from oca

        Param:
            - tracknum: tracking number

        Returns:
            - List of lists, where each each list contains:
                [date, description]
        """
        # Define request URL
        url = "http://www5.oca.com.ar/ocaepakNet/Views/ConsultaTracking/TrackingConsult.aspx/GetTracking"
    
        # Get page
        try:
            response = requests.post(url, json={"numberOfSend": tracknum}, timeout=10)
        except Exception as inst:
            log.error("providers: _get_oca() requests.post exception = " + type(inst).__name__ + " - " + str(inst.args[0:]))
            return

        # Check for errors
        if response.status_code != 200:
            log.error("providers: get_oca_web() status_code exception = " + str(response.status_code))
            return
        
        raw_data = response.json()

        return_list = []
        for row in raw_data["d"]:
            
            # Format date
            raw_date = row["Date"].replace("/Date(", "").replace(")/", "")
            date = datetime.fromtimestamp(int(raw_date)/1e3, tz=self.timezone).strftime("%Y-%m-%d %H:%M")

            # Format description
            description = row["State"].rstrip()

            # Format location
            location = row["Sucursal"].rstrip()

            # Return data
            return_list.append({
                "date":     date,
                "description":  description,
                "location": location
            })
        return(return_list)
    

if __name__ == "__main__":
    prov = Providers()
    info = prov.get("3654000000000245027", "oca")
    list_text = ""

        # Turns it into string
    for row in info:
        list_text += "{}\n{}\n{}\n\n".format(
            row["date"],
            row["description"],
            row["location"]
        )
    print(list_text)
