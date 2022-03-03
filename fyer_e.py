# pip install fyers-apiv2
# pip install selenium
# pip install webdriver-manager
# pip install xlwings
# xlwings addin install

from fyers_api.Websocket import ws
from fyers_api import fyersModel
from fyers_api import accessToken
import xlwings as xw
import datetime
import time
import document_file
from selenium import webdriver
from webdriver_manager.firefox import GeckoDriverManager

log_path = document_file.log_path
client_id = document_file.client_id
secret_key = document_file.secret_key
redirect_url = document_file.redirect_url
response_type = document_file.response_type
grant_type = document_file.grant_type
username = document_file.username
password = document_file.password
pin1 = document_file.pin1
pin2 = document_file.pin2
pin3 = document_file.pin3
pin4 = document_file.pin4

exchange = "NSE"
sheet = xw.Book("F:/fyer/fyer.xlsx").sheets[0]
tickerlist = sheet.range("A2").expand("down").value
sheet.range("B1:M300").clear_contents()
buy_traded_stocks = []
sell_traded_stocks = []

def getTime():
	return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def custom_message(message):
	# print(message[0]['symbol'], message[0]["ltp"], message[0]["high_price"],message[0]["low_price"],message[0]["open_price"],message[0]['close_price'],message[0]["vol_traded_today"])
	sheet = xw.Book("F:/fyer/fyer.xlsx").sheets[0]
	sheet.range("A1").value = [
		"Script", "Ltp", "High", "Low", "Open", "P.Close", "Volume",
		"Condition", "Order_Type", "Quantity", "Order_Status"
	]

	for i in tickerlist:
		if i != None:
			if i.upper() == message[0]['symbol'][4:]:
				cell_no = tickerlist.index(i) + 2
				sheet.range(f"B{cell_no}").value = message[0]["ltp"]
				sheet.range(f"C{cell_no}").value = message[0]["high_price"]
				sheet.range(f"D{cell_no}").value = message[0]["low_price"]
				sheet.range(f"E{cell_no}").value = message[0]["open_price"]
				sheet.range(f"F{cell_no}").value = message[0]['close_price']
				sheet.range(f"G{cell_no}").value = message[0]["vol_traded_today"]

	for i in range(2, (len(tickerlist)+2)):
		Status = sheet.range('I' + str(i)).value
		quantity = sheet.range('J' + str(i)).value
		if (Status != None) & (type(Status) != float) & (type(Status) != int) & (quantity != None) & (type(quantity) != str):
			if (quantity > 0):
				Status = Status.upper()
				quantity = int(quantity)
				Script = sheet.range('A' + str(i)).value
				Script = Script.upper()
				price = sheet.range('B' + str(i)).value

				if (Script not in buy_traded_stocks) and (Status == "BUY"):
					order = fyers.place_order({"symbol":f"{exchange}:{Script}","qty":quantity,"type":"1","side":"1","productType":"INTRADAY","limitPrice":price,"stopPrice":"0","disclosedQty":"0","validity":"DAY","offlineOrder":"False","stopLoss":"0","takeProfit":"0"})
					print(f"Buy Order  Placed for {Script}, at Price: {price} for Quantity: {quantity} at time: {datetime.datetime.now()}")
					buy_traded_stocks.append(Script)
					sheet.range(f"K{i}").value = "Order Placed"
					sheet.range(f"K{i}").autofit()

				if (Script not in sell_traded_stocks) and (Status == "SELL"):
					order = fyers.place_order({"symbol":f"{exchange}:{Script}","qty":quantity,"type":"1","side":"-1","productType":"INTRADAY","limitPrice":price,"stopPrice":"0","disclosedQty":"0","validity":"DAY","offlineOrder":"False","stopLoss":"0","takeProfit":"0"})
					print(f"Sell Order  Placed for {Script}, at Price: {price} for Quantity: {quantity} at time: {datetime.datetime.now()}")
					sell_traded_stocks.append(Script)
					sheet.range(f"K{i}").value = "Order Placed"
					sheet.range(f"K{i}").autofit()
				else:
					# print(f"Order Already Placed for {Script}")
					pass

def generate_access_token(auth_code, appId, secret_key):
	appSession = accessToken.SessionModel(client_id=appId, secret_key=secret_key,grant_type="authorization_code")
	appSession.set_token(auth_code)
	response = appSession.generate_token()["access_token"]
	return response

def generate_auth_code():
	url = f"https://api.fyers.in/api/v2/generate-authcode?client_id={client_id}&redirect_uri={redirect_url}&response_type=code&state=state&scope=&nonce="
	driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
	# driver = webdriver.Firefox(executable_path=r"C:\Users\tradi\.wdm\drivers\geckodriver\win64\v0.30.0\geckodriver.exe")
	driver.get(url)
	time.sleep(8)
	driver.execute_script(f"document.querySelector('[id=fy_client_id]').value = '{username}'")
	driver.execute_script("document.querySelector('[id=clientIdSubmit]').click()")
	time.sleep(8)
	driver.execute_script(f"document.querySelector('[id=fy_client_pwd]').value = '{password}'")
	driver.execute_script("document.querySelector('[id=loginSubmit]').click()")
	time.sleep(8)
	driver.find_element_by_id("verify-pin-page").find_element_by_id("first").send_keys(pin1)
	driver.find_element_by_id("verify-pin-page").find_element_by_id("second").send_keys(pin2)
	driver.find_element_by_id("verify-pin-page").find_element_by_id("third").send_keys(pin3)
	driver.find_element_by_id("verify-pin-page").find_element_by_id("fourth").send_keys(pin4)
	driver.execute_script("document.querySelector('[id=verifyPinSubmit]').click()")
	time.sleep(8)
	newurl = driver.current_url
	auth_code = newurl[newurl.index('auth_code=')+10:newurl.index('&state')]
	driver.quit()
	return auth_code

def main():
	global fyers

	auth_code = generate_auth_code()
	access_token = generate_access_token(auth_code, client_id, secret_key)
	fyers = fyersModel.FyersModel(token=access_token, log_path=log_path, client_id=client_id)
	fyers.token = access_token
	print("Access Token Successfully Generated")
	newtoken = f"{client_id}:{access_token}"
	data_type = "symbolData"

	symbol = []
	for i in tickerlist:
		i = i.upper()
		symbol.append(f"{exchange}:{i}")
	
	fs = ws.FyersSocket(access_token=newtoken,run_background=False,log_path=log_path)
	fs.websocket_data = custom_message
	fs.subscribe(symbol=symbol,data_type=data_type)
	fs.keep_running()

if __name__ == "__main__":
	main()