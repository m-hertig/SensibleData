import gmail, time, unicodedata

while True:
	g = gmail.login("sensibledata2@gmail.com", "verysensible")
	unread = g.inbox().mail(unread=True)
	if len(unread)>0: 
		# None

		unread[0].fetch()
		sender = unread[0].fr
		senderNormalized = unicodedata.normalize('NFKD', sender).encode('ascii', 'ignore')
		unread[0].read()
		# Dear ...,
	time.sleep(4)
	g.logout()