#! /usr/bin/env python3

from papirus import PapirusComposite
import requests
from signal import pause
from gpiozero import Button
from time import sleep

class Display:
    def __init__(self, file_path, coin_limit):
        """
        :param file_path: path to list of coins to check, not greater than coin_limit
        """
        self.url = 'https://coincap.io'
        self.coin_file_path = file_path
        self.coin_limit = coin_limit
        self.driver = PapirusComposite(False, rotation=0)  # if false, will wait until writeall is called
        self.uparrow_path = ''
        self.downarrow_path = ''
        self.fontsize = 13
        self.debug = True
        self.coinprice_list = []
        self.sw1 = Button(21, pull_up=False)
        self.sw2 = Button(16, pull_up=True)
        self.sw3 = Button(20, pull_up=True)
        self.sw4 = Button(19, pull_up=True)
        self.sw5 = Button(26, pull_up=True)

    def draw_image(self, image_path, posX, posY, width, height, picture_id):
        """
        draws an image
        """

        self.driver.AddImg(image=str(image_path), x=posX, y=posY, size=(width, height), Id=str(picture_id))

    def update_image(self, image_path, picture_id):
        """
        updates an image
        """

        self.driver.UpdateImg(image=str(image_path), Id=str(picture_id))

    def remove_image(self, picture_id):
        """
        removes an image
        """

        self.driver.RemoveImg(Id=str(picture_id))

    def draw_text(self, text, posX, posY, fontsize, text_id, fontpath=None):
        """
        draws text
        """

        self.driver.AddText(text=str(text), x=posX, y=posY, size=fontsize, Id=str(text_id))

    def update_text(self, text, text_id, fontpath=None):
        """
        updates text
        """

        self.driver.AddText(newText=str(text), Id=str(text_id))

    def remove_text(self, text_id):
        """
        removes text
        """

        self.driver.RemoveText(Id=str(text_id))

    def write_screen(self):
        """
        writes data to screen
        """

        self.driver.WriteAll()

    def call_api(self, endpoint, coin_name):
        # todo: move this to an async external module, write data to a file, fiunction below grabs this file
        """
        Calls the api
        :param endpoint: the api call i.e history, 1day
        :param coin_name: ticket name of coin i.e ETH
        :return: json
        """
        try:
            request = "{url}/{endpoint}/{coin_name}".format(
                    url=self.url,
                    endpoint=endpoint,
                    coin_name=coin_name.upper()
                )

            # wish debian kept up with the times so I can use f strings
            response = requests.get(request)

            if self.debug:
                print(request)

            return response.json()

        except Exception as e:
            print(e)

    def get_currentprice(self, coin):
        """
        Gets the price for a single coin

        :param coin: string e.g ETH
        :return: price in USD and ETH: tuple(float, float)
        """
        response = self.call_api(endpoint="page", coin_name=coin)
        price_usd = "${}".format(response.get("price_usd"))
        price_eth = "e{}".format(response.get("price_eth"))

        # lazy handling if coin doesn't have eth price, just return USD
        if response.get("price_eth") is None:
            price_eth = price_usd

        return price_usd, price_eth

    def print_this(self, switch):
        print(switch)
        self.draw_text(text=switch, posX=0, posY=0, fontsize=self.fontsize, text_id=switch)
        self.write_screen()

    def main(self):
        """
        The bread and butter
        """
        print('started')
        # need to use reverse logic because the hat buttons are set high
        while True:
            if not self.sw1.is_active:
                print('true')
                break

        # from file list, get coins
        with open(self.coin_file_path, 'r') as file:
            file_contents = file.readlines()

        # cant display more than 14 coins
        if len(file_contents) > 14:
            raise Exception("Too many coins to list {} > 14".format(len(file_contents)))

        # for each coin in list, write text to a new line
        # create an 8x2 grid

        posx = 0
        posy = 0
        coin_count = 0
        next_grid = 0

        for line in file_contents:

            # split the line into two elements
            coin = ''.join(line).split(',')

            try:
                if self.debug:
                    print("Coin: {}, Format: {}".format(coin[0], coin[1]))
                    print("X: {}, Y: {}".format(posx, posy))
                    print("count: {}, grid: {} \n\n".format(coin_count, next_grid))

                # get the prices
                price_usd, price_eth = self.get_currentprice(coin[0])

                # once the counter gets to 6, draw the next grid, shift 100 px right, reset Y
                if coin_count > 6 and next_grid is 0:
                    posx = 100
                    posy = 0
                    coin_count = 0
                    next_grid = 1

                # check if the coin should be displyed in eth or usd
                # use one conditional for a marginal speed up
                texttoprint = "{coin} {price}".format(coin=coin[0].upper(), price=str(price_eth)[:7])

                if 'usd' in coin[1]:
                    texttoprint = "{coin} {price}".format(coin=coin[0].upper(), price=str(price_usd)[:7])

                # draw the text
                self.draw_text(text=texttoprint, posX=posx, posY=posy, fontsize=self.fontsize, text_id=coin[0])

                # increment counters
                posy += 13
                coin_count += 1

            except IndexError:
                pass
                # cheap way to stop index out of range if there are blank lines

        # get the last candle or something
        last_candle = ''
        # write up or down to file
        with open('candles.txt', 'a') as candle_file:
            candle_file.writelines("{}".format(last_candle))
        # or compare the number to the previous, then you know if up or down
        self.write_screen()


if __name__ == "__main__":
    coin_file_path = "coinlist.txt"
    display = Display(file_path=coin_file_path, coin_limit=14)
    display.main()
