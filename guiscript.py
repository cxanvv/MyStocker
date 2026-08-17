import tkinter as t
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from tkinter import filedialog,messagebox as msgbox

import copy
from datetime import datetime

import logic
import json
import os

class GuiScript():
    def __init__(self,w,gui):
        self.w = w
        self.gui = gui
        self.TempSaleItems = []
        self.JsonData = { # Data template
            "Settings" : {
                "OperatingDays" : 1
            },
            "Stock" : [],
            "Sale" : []
        }
        self.OldJsonData = copy.deepcopy(self.JsonData) # to check for saving
        self.SelectedSavePath = None
    def OnClosing(self):
        if self.OldJsonData != self.JsonData:
            savemsg = msgbox.askyesnocancel(message='Save before closing?')
            if savemsg is True:
                self.Save() if self.SelectedSavePath else self.NewSave()
            elif savemsg is None:
                return
        self.w.destroy()
    def NotebookTabChange(self,event):
        notebook = event.widget
        selected_tab = notebook.select()
        
        if selected_tab == str(self.gui.MainFrame):
            self.UpdateDataGui()
    def UpdateDataGui(self):
        # stock
        self.gui.StockList.delete(*self.gui.StockList.get_children())
        self.gui.SaleList.delete(*self.gui.SaleList.get_children())
        for n,stock in enumerate(self.JsonData['Stock']):
            buycost = f"{stock['BuyCost']:,}" + f"/{stock['Measurement']}" if stock['PriceMethod'] == 'Measured' else f"{stock['BuyCost']:,}"
            saleprice = f"{stock['SalePrice']:,}"
            quantity = f"{stock['Quantity']:,}"
            if stock['PriceMethod'] == 'Measured':
                saleprice += f"/{stock['Measurement']}"
                quantity += f" {stock['Measurement']}"
            elif stock['PriceMethod'] == 'Custom':
                saleprice = 'Custom'
            self.gui.StockList.insert('',t.END,text=n+1,values=(stock['Name'],quantity,buycost,saleprice))
        
        # sale
        saleProfit = 0
        for n,sale in enumerate(self.JsonData['Sale']):
            ItemSaleCount = len(sale['Items'])
            FirstSaleItem = sale['Items'][0]
            FirstItemQuantityDisplay = f"{FirstSaleItem['Quantity']:,}x"
            if FirstSaleItem['PriceMethod'] == 'Measured':
                FirstItemQuantityDisplay = f"{FirstSaleItem['Quantity']:,} {FirstSaleItem['Measurement']}"
            itemsTxt = f"{FirstItemQuantityDisplay} {FirstSaleItem['Name']}" if ItemSaleCount == 1 else f"{FirstItemQuantityDisplay} {FirstSaleItem['Name']}... (+{ItemSaleCount-1})"
            totalPrice = 0
            saleProfit += sale['Profit']
            for item in sale['Items']:
                totalPrice += item['Price']
            self.gui.SaleList.insert('',t.END,text=n+1,values=(sale['Date'],itemsTxt,f"{totalPrice:,}",f"{sale['Profit']:,}"))
        self.gui.ProfitTotalText.config(text=f'Total Profit: {saleProfit:,}')

        # settings
        self.gui.OperatingDaysTitle.config(text=f"Operating days per week: {self.JsonData['Settings']['OperatingDays']}")
        self.gui.OperatingDaysInput.set(self.JsonData['Settings']['OperatingDays'])

        # main
        SalesSummary = {} # format>> Date: total profit, customers, sales
        OrderedDateIndex = []
        AllCustomers = 0
        AllProfit = 0
        for s in self.JsonData['Sale']:
            if s['Date'] not in SalesSummary:
                SalesSummary[s['Date']] = {
                    'TotalProfit' : s['Profit'],
                    'Customers' : 1,
                    'Sales' : sum(item['Quantity'] for item in s['Items'])
                }
                OrderedDateIndex.append(s['Date'])
            else:
                SalesSummary[s['Date']]['TotalProfit'] += s['Profit']
                SalesSummary[s['Date']]['Customers'] += 1
                SalesSummary[s['Date']]['Sales'] += sum(item['Quantity'] for item in s['Items'])
            AllCustomers += 1
            AllProfit += s['Profit']
        OrderedDateIndex.sort(key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        deltaDays = logic.DeltaDateInDays(OrderedDateIndex[0],OrderedDateIndex[-1]) + 1 if len(OrderedDateIndex) > 0 else 0

        # Count for total days
        OperatingDaysPerWeek = self.gui.OperatingDaysInput.get()
        deltaWeeks = deltaDays//7
        Days = len(OrderedDateIndex) if deltaDays < 7 and deltaDays > OperatingDaysPerWeek else (deltaWeeks * OperatingDaysPerWeek) + min(deltaDays-deltaWeeks*7,OperatingDaysPerWeek)
        
        AllSales = sum(SalesSummary[salesum]['Sales'] for salesum in SalesSummary)
        avgcustomers = round(AllCustomers/Days) if Days > 0 else 0
        avgprofit = round(AllProfit/Days) if Days > 0 else 0
        avgitemssold = round(AllSales/Days) if Days > 0 else 0
        self.gui.AvgCustomers.config(text=f'Average customers: {avgcustomers:,}/day')
        self.gui.AvgProfit.config(text=f'Average profit: {avgprofit:,}/day')
        self.gui.AvgItemsSold.config(text=f'Average items sold: {avgitemssold:,}/day')
        
    def CloseWindowOpenMain(self,window):
        window.destroy()
        self.w.deiconify()
    def NewStockGui(self):
        self.w.withdraw()
        self.gui.NewStockGui()
    def UpdateStockGui(self):
        selected_stocks = self.gui.StockList.selection()
        if len(selected_stocks) == 0:
            msgbox.showwarning('Error','Please select a stock.')
            return
        self.w.withdraw()
        self.gui.UpdateStockGui()
    def NewSaleHGui(self):
        self.TempSaleItems.clear()
        self.w.withdraw()
        self.gui.NewSaleHGui()
    def GetTreeviewSelectedItem(self,treeview):
        selected_elements = treeview.selection()
        raw_data = treeview.item(selected_elements[0],'values')
        return raw_data
    def UpdateDataInUpdStockGui(self):
        stockdata = logic.GetDictFromListWithKeyValue(self.JsonData["Stock"],"Name",self.GetTreeviewSelectedItem(self.gui.StockList)[0])
        self.gui.NameInput.insert(0,stockdata['Name'])
        self.gui.QuantityInput.insert(0,stockdata['Quantity'])
        self.gui.BuyInput.insert(0,stockdata['BuyCost'])
        if stockdata['PriceMethod'] == 'Custom':
            self.gui.SaleInput.configure(bootstyle='danger')
            self.gui.SaleInput.insert(0,'Custom')
            self.gui.SaleInput.configure(state='disabled')
        else:
            self.gui.SaleInput.insert(0,stockdata['SalePrice'])
        self.gui.NoteInput.insert(0,stockdata['Note'])
        self.gui.QuantityInput.config(state='readonly')
    def StockPricingMethodSelect(self,event):
        method = event.widget.get()
        self.gui.MeasurementInpText.grid_forget()
        self.gui.MeasurementInput.grid_forget()
        self.gui.SaleInput.configure(bootstyle='default')
        self.gui.SaleInput.configure(state='normal')
        if method == 'Measured':
            self.gui.MeasurementInpText.grid(column=0,row=3,sticky='w',padx=15,pady=2)
            self.gui.MeasurementInput.grid(column=1,row=3,sticky='w',pady=2)
        if method == 'Custom':
            self.gui.SaleInput.configure(bootstyle='danger')
            self.gui.SaleInput.insert(0,'Custom')
            self.gui.SaleInput.configure(state='disabled')
    def DoAddStock(self):
        StockName = self.gui.NameInput.get()
        Quantity = self.gui.QuantityInput.get()
        PMethod = self.gui.PricingMethod.get()
        Measurement = self.gui.MeasurementInput.get()
        BuyCost = self.gui.BuyInput.get()
        SalePrice = self.gui.SaleInput.get()
        Date = self.gui.StockDateInput.entry.get()
        Note = self.gui.NoteInput.get()
        if logic.GetDictFromListWithKeyValue(self.JsonData['Stock'],'Name',StockName):
            msgbox.showerror('Error','Stock name already in use. Please enter a different name.')
            return
        if StockName == '':
            msgbox.showerror('Invalid Input','Please enter a valid stock name.')
            return
        if not Quantity.isdigit():
            msgbox.showerror('Invalid Input','Please enter a valid number in the quantity box.')
            return
        if not BuyCost.isdigit():
            msgbox.showerror('Invalid Input','Please enter a valid number in the buy cost box.')
            return
        if not SalePrice.isdigit() and PMethod != 'Custom':
            msgbox.showerror('Invalid Input','Please enter a valid number in the sale price box.')
            return
        try:
            datetime.strptime(Date, '%d/%m/%Y')
        except:
            msgbox.showerror('Invalid Input','Please enter a valid date in the date box.')
            return
        stockdata = {
            "Name" : StockName,
            "Quantity" : int(Quantity),
            "BuyCost" : int(BuyCost),
            "SalePrice" : int(SalePrice) if PMethod != 'Custom' else -1,
            "PriceMethod" : PMethod,
            "Measurement" : Measurement,
            "StockDate" : Date,
            "Note" : Note
        }
        self.JsonData["Stock"].append(stockdata)
        self.UpdateDataGui()
        self.gui.NewStockWindow.destroy()
    def DoUpdStock(self):
        StockName = self.gui.NameInput.get()
        AddQuantity = self.gui.AddQuantityInput.get()
        BuyCost = self.gui.BuyInput.get()
        SalePrice = self.gui.SaleInput.get()
        Note = self.gui.NoteInput.get()
        stockdata = self.JsonData["Stock"]
        indextarget = stockdata.index(logic.GetDictFromListWithKeyValue(stockdata,"Name",self.GetTreeviewSelectedItem(self.gui.StockList)[0]))
        datatarget = stockdata[indextarget]
        if not AddQuantity.isdigit():
            msgbox.showerror('Invalid Input','Please enter a valid number in the additional quantity box.')
            return
        if not BuyCost.isdigit():
            msgbox.showerror('Invalid Input','Please enter a valid number in the buy cost box.')
            return
        if not SalePrice.isdigit() and datatarget["PriceMethod"] != "Custom":
            msgbox.showerror('Invalid Input','Please enter a valid number in the sale price box.')
            return
        yesno = msgbox.askyesno('Update Stock','Update Stock?')
        if not yesno: return
        datatarget["Name"] = StockName
        datatarget["Quantity"] += int(AddQuantity)
        datatarget["BuyCost"] = int(BuyCost)
        datatarget["SalePrice"] = int(SalePrice) if datatarget["PriceMethod"] != "Custom" else -1
        datatarget["Note"] = Note
        self.UpdateDataGui()
        self.gui.UpdStockWindow.destroy()
    def DeleteStock(self):
        yesno = msgbox.askyesno('Delete Stock','Are you absolutely sure you want to DELETE this stock? (This cannot be undone and will not affect your sale history)')
        if not yesno: return
        datatarget = logic.GetDictFromListWithKeyValue(self.JsonData["Stock"],"Name",self.GetTreeviewSelectedItem(self.gui.StockList)[0])
        self.JsonData["Stock"].remove(datatarget)
        self.UpdateDataGui()
        self.gui.UpdStockWindow.destroy()
    def DoAddSaleItem(self):
        Item = self.gui.ItemInput.get()
        Quantity = self.gui.ItemQuantity.get()
        ItemInfo = logic.GetDictFromListWithKeyValue(self.JsonData['Stock'],'Name',Item)
        if not ItemInfo:
            msgbox.showerror('Invalid Input','Item not found.')
            return
        if not Quantity.isdigit():
            msgbox.showerror('Invalid Input','Please enter a valid number in the item quantity box.')
            return
        Quantity = int(Quantity)
        QuantityDisplay = f"{Quantity:,}x"
        if Quantity == 0:
            msgbox.showerror('Invalid Input','Please enter a valid number in the item quantity box.')
            return
        if Quantity > self.JsonData["Stock"][self.JsonData["Stock"].index(ItemInfo)]["Quantity"]:
            msgbox.showwarning('Out of Stock','The sales quantity exceeds stock quantity. Please check the stock quantity.')
            return
        all_items = [self.gui.ItemList.set(child, "Name") for child in self.gui.ItemList.get_children()]
        if Item in all_items:
            msgbox.showwarning('Error','Item already added in the list, select and delete the item if you want to change.')
            return
        saleprice = Quantity * ItemInfo['SalePrice']
        if ItemInfo['PriceMethod'] == 'Custom':
            CustomStatus, CustomPrice = self.gui.CustomPriceGui()
            if CustomStatus:
                if not CustomPrice.isdigit():
                    msgbox.showerror('Invalid Input','Please enter a valid number.')
                    return
                saleprice = Quantity * int(CustomPrice)
            else: return
        elif ItemInfo['PriceMethod'] == 'Measured':
            QuantityDisplay = f"{Quantity:,} {ItemInfo['Measurement']}"
        self.TempSaleItems.append(
            {
                'Name' : Item,
                'Quantity' : Quantity,
                'Price' : saleprice,
                'PriceMethod' : ItemInfo['PriceMethod'],
                'Measurement' : ItemInfo['Measurement']
            }
        )
        self.gui.ItemList.insert('',t.END,text=len(self.gui.ItemList.get_children())+1,values=(ItemInfo['Name'],QuantityDisplay,f"{saleprice:,}"))
    def DoDeleteSaleItem(self):
        item_selections = self.gui.ItemList.selection()
        if len(item_selections) == 0:
            msgbox.showerror('Error','Select an item from the item list box first.')
            return
        self.TempSaleItems.remove(logic.GetDictFromListWithKeyValue(self.TempSaleItems,'Name',self.gui.ItemList.item(item_selections[0])['values'][0]))
        self.gui.ItemList.delete(item_selections[0])
        ids = self.gui.ItemList.get_children()
        Items = []
        for item_id in ids:
            Items.append(self.gui.ItemList.item(item_id)['values'])
        self.gui.ItemList.delete(*ids)
        for item in Items:
            self.gui.ItemList.insert('',t.END,text=len(self.gui.ItemList.get_children())+1,values=item)
    def UpdateDataInNewSaleGui(self):
        stocks = []
        for stock in self.JsonData['Stock']:
            stocks.append(stock['Name'])
        self.gui.ItemInput.config(values=stocks)
    def ItemSaleSelect(self,event):
        item = event.widget.get()
        ItemInfo = logic.GetDictFromListWithKeyValue(self.JsonData['Stock'],'Name',item)
        Quantity = ItemInfo['Quantity']
        Price = f"{ItemInfo['SalePrice']:,}"
        QuantityDisplay = f"{ItemInfo['Quantity']:,}x"
        if ItemInfo['PriceMethod'] == 'Measured':
            Price += f"/{ItemInfo['Measurement']}"
            QuantityDisplay = f"{ItemInfo['Quantity']:,} {ItemInfo['Measurement']}"
        elif ItemInfo['PriceMethod'] == 'Custom':
            Price = 'Custom'
        if ItemInfo:
            self.gui.ItemPriceText.config(text=f"Price per item: {Price}\nQty: {QuantityDisplay}")
            if Quantity == 0:
                self.gui.ItemPriceText.configure(bootstyle='danger')
            else:
                self.gui.ItemPriceText.configure(bootstyle='default')
        else:
            self.gui.ItemPriceText.config(text='Please select an item.')
    def DoAddSaleHistory(self):
        Note = self.gui.NoteInput.get()
        Date = self.gui.DateInput.entry.get()
        ids = self.gui.ItemList.get_children()
        if len(ids) == 0:
            msgbox.showerror('No Items','Cannot make a sale history with empty sold items.')
            return
        try:
            datetime.strptime(Date, '%d/%m/%Y')
        except:
            msgbox.showerror('Invalid Input','Please enter a valid date in the date box.')
            return
        Profit = 0
        for item in self.TempSaleItems:
            ItemInfo = logic.GetDictFromListWithKeyValue(self.JsonData["Stock"],"Name",item["Name"])
            self.JsonData["Stock"][self.JsonData["Stock"].index(ItemInfo)]["Quantity"] -= item["Quantity"]
            Profit += item["Price"] - ItemInfo["BuyCost"] * item["Quantity"]
        saledata = {
            "Items" : self.TempSaleItems.copy(),
            "Profit" : Profit,
            "Date" : Date,
            "Note" : Note
        }
        self.JsonData["Sale"].append(saledata)
        self.UpdateDataGui()
        self.gui.NewSaleHWindow.destroy()
    def UpdateSaleGui(self):
        selected_sales = self.gui.SaleList.selection()
        if len(selected_sales) == 0:
            msgbox.showwarning('Error','Please select a sale history.')
            return
        self.w.withdraw()
        self.gui.UpdateSaleGui()
    def DoUpdSaleHistory(self):
        saledata = self.JsonData['Sale'][self.gui.SaleList.index(self.gui.SaleList.selection()[0])]
        Note = self.gui.NoteInput.get()
        Date = self.gui.DateInput.entry.get()
        try:
            datetime.strptime(Date, '%d/%m/%Y')
        except:
            msgbox.showerror('Invalid Input','Please enter a valid date in the date box.')
            return
        yesno = msgbox.askyesno('Update Sale History','Update Sale History?')
        if not yesno: return
        saledata["Date"] = Date
        saledata["Note"] = Note
        self.UpdateDataGui()
        self.gui.UpdSaleWindow.destroy()
    def UpdateDataInUpdSaleGui(self):
        saledata = self.JsonData['Sale'][self.gui.SaleList.index(self.gui.SaleList.selection()[0])]
        for n,item in enumerate(saledata['Items']):
            self.gui.ItemList.insert('',t.END,text=str(n+1),values=(item['Name'],f"{item['Quantity']:,}x",f"{item['Price']:,}"))
        self.gui.DateInput.entry.delete(0, 'end')
        self.gui.DateInput.entry.insert(0,saledata['Date'])
        self.gui.NoteInput.insert(0,saledata['Note'])
    def DoDeleteSaleHistory(self):
        yesno = msgbox.askyesno('Delete Sale History','Are you absolutely sure you want to DELETE this history? (This cannot be undone and the sold stock will not be replenished)')
        if not yesno: return
        datatarget = self.JsonData['Sale'][self.gui.SaleList.index(self.gui.SaleList.selection()[0])]
        self.JsonData["Sale"].remove(datatarget)
        self.UpdateDataGui()
        self.gui.UpdSaleWindow.destroy()
    def SettingsOperatingDaysScale(self,new):
        new = round(float(new))
        self.JsonData['Settings']['OperatingDays'] = new
        self.gui.OperatingDaysTitle.config(text=f'Operating days per week: {new}')
    def NewSave(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All Files", "*.*")],
            initialfile='MyStocker'
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.JsonData, f, indent=4)
                    self.gui.w.title(f'MyStocker - {os.path.basename(f.name)}')
                    self.SelectedSavePath = f.name
                    self.gui.SelectedFileInfo.config(text=f'{f.name}')
                self.OldJsonData = copy.deepcopy(self.JsonData)
                msgbox.showinfo("Success", f"Data successfully saved to {file_path}")
            except Exception as e:
                msgbox.showerror("Error", e)
    def Save(self):
        if self.SelectedSavePath:
            try:
                with open(self.SelectedSavePath, 'w') as f:
                    json.dump(self.JsonData, f, indent=4)
                self.OldJsonData = copy.deepcopy(self.JsonData)
            except Exception as e:
                msgbox.showerror("Error", e)
        else:
            self.NewSave()
    def OpenFile(self):
        if self.OldJsonData != self.JsonData:
            savemsg = msgbox.askyesnocancel(message='Save before opening a new file?')
            if savemsg is True:
                self.Save() if self.SelectedSavePath else self.NewSave()
            elif savemsg is None:
                return
        filepath = filedialog.askopenfilename(
            title="Open a JSON File",
            initialdir="/",
            filetypes=[("JSON files", "*.json"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    self.JsonData = json.load(f)
                    self.gui.w.title(f'MyStocker - {os.path.basename(f.name)}')
                    self.SelectedSavePath = f.name
                    self.gui.SelectedFileInfo.config(text=f'{f.name}')
                self.OldJsonData = copy.deepcopy(self.JsonData)
                self.UpdateDataGui()
            except json.JSONDecodeError:
                msgbox.showerror("Error", 'JSON decode error')
            except Exception as e:
                msgbox.showerror("Error", e)
