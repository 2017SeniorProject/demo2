import py2neo
from py2neo import Graph, Node, Relationship
from datetime import datetime
import requests
import json
import random

#open Graph database
graph=Graph("localhost")  #depend on your authorization choice

class User:
	def __init__(self, username):
		self.username = username
	
	def find(self):
		user = graph.find_one('User', 'username', self.username)
		return user

	def register(self, password):
		if not self.find():
			user = Node('User', username=self.username, password=password)
			graph.create(user)
			return True
		else:
			return False
	
	def verify_password(self, password):
		user = self.find()
		if user:
			return (password==user['password'])
		else:
			return False

	def search_interest(self,reco):
		user=self.find()
		list_res1=list(reco)
		length=len(list_res1)

		if length>0:
			if length>=1 and length<=3:
				list_res=list_res1.copy()
			if length>3:
				list_res=[0]*3
				for i in range(3):
					no=random.randint(0,length-1)
					list_res[i]=list_res1[no]
							
			for i in range(len(list_res)):
				res=graph.find_one("Restaurant","shopId",list_res[i]['reco']['shopId'])
				relation=graph.match_one(start_node=user,rel_type='INTEREST',end_node=res,bidirectional=False)
				if(relation==None):
					rel = Relationship(user, 'INTEREST',res,level=1)
					graph.create(rel)
				else:
					relation["level"]=relation["level"]+1
					graph.push(relation)
		return 1
	
	def setLocation(self):
		user=self.find()

		send_url = 'http://freegeoip.net/json'
		r = requests.get(send_url)
		j = json.loads(r.text)

		user["latitude"] = j['latitude']
		user["longitude"] = j['longitude']

		graph.push(user)


class RecoEngine:
	def res_near_you():
		#send url to get your current location #can use better method to get the division automatically as well
		send_url = 'http://freegeoip.net/json'
		r = requests.get(send_url)
		j = json.loads(r.text)
		lati = j['latitude']
		longi = j['longitude']

		#query for the match your location with the restaurant
		query='''
		WITH point({latitude:{lat},longitude:{lon}}) AS mapcenter
		   MATCH (reco:Restaurant)-[:IN_DIVISION]->(b:Division) 
		   WITH reco, distance (point({latitude: reco.latitude, longitude: reco.longitude}), mapcenter) AS distance
		   RETURN reco, distance
		   ORDER BY distance LIMIT 5
		'''
		lat=24.8229533748
		lon=121.771853579
		#sdivision=location
		return graph.run(query,lat=lat,lon=lon)


	def res_by_month(location,month1):
		#input month, division, average
		month=int(month1)
		division=location

		query='''
		match (d:Division{e_name:"Jiaoxi Township"})-[:IN_MONTH]->(m:Month{month:{month}}),
			(m)<-[:WRITTEN_IN]-(r:Review),
		    (r)-[:ABOUT]->(n:Restaurant)
		return avg(r.SDRate) as avg
		'''
		avg_data=graph.run(query,month=month,division=location).data()

		average=avg_data[0]['avg']

		#recommendation for restaurant by month: ranking the the restaurant by their review rating: most review above average of month
		query='''
		match (d:Division{e_name:{division}})-[:IN_MONTH]->(m:Month{month:{month}})
		match	(m)<-[:WRITTEN_IN]-(r:Review)
		match   (r)-[:ABOUT]->(reco:Restaurant) where r.SDRate>{average}
		return reco, count(r) as count order by count desc
		'''
		return graph.run(query,month=month,division=location,average=average)


	def res_general_rec(location,category):
		#category="其他小吃"
		#division="Jiaoxi Township"

		query='''
		match(reco:Restaurant)-[:IN_DIVISION]-(d:Division),
		(reco)-[:IN_CATEGORY]->(c:Category)
		where c.SDCategory={category} and
			d.e_name={division}
		return reco order by reco.SDRate desc limit 20
		'''
		return graph.run(query,category=category,division=location)

	def res_similiar_search(location1,category1):
		#category="其他小吃"
		#division="Jiaoxi Township"
		category=category1
		division=location1

		query='''
		match(n:Restaurant)-[:IN_DIVISION]-(d:Division),
		(n)-[:IN_CATEGORY]->(c:Category)
		where c.SDCategory={category} and
			d.e_name={division}
		with collect(n) as exclude,collect(c) as rec_cat
		match (reco)-[:IN_CATEGORY]->(c1:Category)
		where NOT reco IN exclude and
			 c1 IN rec_cat
		return reco order by reco.SDRate desc
		'''
		return graph.run(query,category=category,division=division)

	def res_relating_search(location1,category1):
		#input month, division from users(should be saved during the user session to do the recommendation)
		#category="其他小吃"
		#division="Luodong Township"
		category=category1
		division=location1

		# get the search data
		query='''
		match(n:Restaurant)-[:IN_DIVISION]-(d:Division),
		(n)-[:IN_CATEGORY]->(c:Category)
		where c.SDCategory={category} and
			d.e_name={division}
		return n.shopId    
		'''
		search=graph.run(query,category=category,division=division).data()

		#just get the first on in the list to travel around its neighbor to get recommendation  

		input1=search[0]['n.shopId']
		query='''
		match (n:Restaurant{shopId:{input1}}),
		path=(n)-[r:RELATE*1..2]-(reco)
		with reduce(common_au=0, r IN rels(path) | common_au+r.common_au) AS totalWeight,path,(n),(reco)
		return reco,totalWeight order by totalWeight desc limit 20
		'''
		return graph.run(query,input1=input1)

#####################################################################################################################
	def res_general_rec1(location,category,month1):
		#category="其他小吃"
		#division="Jiaoxi Township"
		#month=int(month1)

		if category=="":
			in_category=""
		else:
			in_category="""and c.SDCategory={category}"""

		if month1=="":
			in_month=""
		else:
			month=month1
			in_month="and rel.month_tendency=1 and m.month= "+month+" "

		begin="""Match (reco:Restaurant)-[:IN_DIVISION]->(d:Division),
				(reco)-[rel:GOOD_IN]->(m:Month),
				(reco)-[:IN_CATEGORY]->(c:Category)
			    where d.e_name={division}"""
		end=" return (reco) order by reco.SDRate limit 20"

		query=begin+in_month+in_category+end
		
		return graph.run(query,division=location,category=category)

	def res_similiar_search1(user1):

		user=user1.find()
		username=user['username']
		query="""
		match p=(u:User)-[rel:INTEREST]->(res:Restaurant) 
		where u.username={username}
		with u, rel, res order by rel.level desc limit 3
		with  collect(res) as interests
		unwind interests as interest
		match (interest)-[:IN_CATEGORY]->(cat:Category),
		(cat)<-[:IN_CATEGORY]-(reco:Restaurant)
		where not reco in interests
		return distinct reco limit 20

		"""
		return graph.run(query,username=username)

	def res_relating_search1(user1):

		user=user1.find()
		username=user['username']		
		query="""
		match p=(u:User)-[rel:INTEREST]->(res:Restaurant) 
		where u.username={username}
		with u, rel, res order by rel.level desc limit 3
		with  collect(res) as interests
		unwind interests as interest
		match (interest)-[:NEIGHBOR*1..5]->(reco:Restaurant) where not reco in interests
		return distinct reco

		"""
		return graph.run(query,username=username)

#########################################################################################
	def top_places1(division):

		query="""
		match (reco:Restaurant)<-[rel:TOP_PLACE]-(d:Division)
			where d.e_name={location}
			with reco,rel.top_place as top_place
			return reco order by top_place desc
		"""
		return graph.run(query,location=division)

	def res_relating_search2(user1):

		user=user1.find()
		username=user['username']	
			
		query1="""
		match p=(u:User)-[rel:INTEREST]->(res:Restaurant) 
		where u.username={username}
		"""

		query="""
		match p=(u:User)-[rel:INTEREST]->(res:Restaurant) 
		where u.username={username} 
		with u, rel, res order by rel.level desc limit 3
		with  collect(res) as interests
		unwind interests as interest
		match (interest)-[:NEIGHBOR*1..5]->(reco:Restaurant) where not reco in interests
		return distinct reco

		"""
		return graph.run(query,username=username)
###############################################################################################
	def res_this_month(loc,cat,user1):
		#find today month
		now=datetime.now()
		month=now.month

		#get the user
		user=user1.find()
		username=user["username"]

		if loc=="":
			in_division=""
		else:
			in_division=" and d.e_name="+"\""+loc+"\" "

		if cat=="":
			in_category=""
		else:
			in_category=" and c.SDCategory="+"\""+cat+"\" "

		#fit in the query
		begin="""
			Match (u:User) where u.username={username}
			WITH point({latitude:u.latitude,longitude:u.longitude}) AS mapcenter

			MATCH (reco:Restaurant)-[:IN_DIVISION]->(d:Division),
				  (reco)-[rel:BY_MONTH]->(m:Month),
				(reco)-[:IN_CATEGORY]->(c:Category) """
		m="where m.month={month} "

		end="""
		 WITH reco, distance (point({latitude: reco.latitude, longitude: reco.longitude}), mapcenter) AS distance ,rel,c
			RETURN distinct reco,distance,c.SDCategory as cat, rel.m_avg as month_score
			ORDER BY month_score desc LIMIT 20
		"""
		query=begin+m+in_division+in_category+end

		return graph.run(query,username=username,month=month)


	def more(loc,cat,mon,user1):
		#get the user
		user=user1.find()
		username=user["username"]

		if loc=="":
			in_division=""
		else:
			in_division=" d.e_name="+"\""+loc+"\" "

		if cat=="":
			in_category=""
		else:
			in_category=" and c.SDCategory="+"\""+cat+"\" "

		if mon=="":
			in_month=""
		else:
			in_month=" and m.month= "+mon+" "

		#fit in query
		begin="""
			Match (u:User) where u.username={username}
			WITH point({latitude:u.latitude,longitude:u.longitude}) AS mapcenter

			MATCH (reco:Restaurant)-[:IN_DIVISION]->(d:Division),
				  (reco)-[rel:BY_MONTH]->(m:Month),
				(reco)-[:IN_CATEGORY]->(c:Category) where """
		
		if mon=="":
			end="""
			WITH distinct reco, distance (point({latitude: reco.latitude, longitude: reco.longitude}), mapcenter) AS distance ,rel,c
				RETURN reco,distance
				ORDER BY reco.SDRate desc LIMIT 20
			"""
		else:

			end="""
			 WITH reco, distance (point({latitude: reco.latitude, longitude: reco.longitude}), mapcenter) AS distance ,rel,c
				RETURN reco,distance, rel.m_avg as month_score
				ORDER BY month_score desc LIMIT 20
			"""

		query=begin+in_division+in_category+in_month+end

		return graph.run(query,username=username)

	def near_you2(user1):
		user=user1.find()
		username=user['username']

		query="""
		Match (u:User) where u.username={username}
		WITH point({latitude:u.latitude,longitude:u.longitude}) AS mapcenter
		MATCH (reco:Restaurant)-[:IN_DIVISION]->(d:Division)

		WITH reco, distance (point({latitude: reco.latitude, longitude: reco.longitude}), mapcenter) AS distance
		RETURN reco, distance
		ORDER BY distance LIMIT 10
		"""
		return graph.run(query,username=username)
############################################################################################################################################
	def relating(shopId):

		idd=int(shopId)
		query="""match(n:Restaurant{shopId:{idd}}),
		path=(n)-[r:NEIGHBOR*1..2]-(reco) 
		with reduce(cost=0,r in rels(path)|cost+r.cost) as totalWeight,path,(n),(reco)
		return distinct reco, totalWeight order by totalWeight limit 5"""

		return graph.run(query,idd=idd)

	def more2(location,category,month,user1):
		user=user1.find()
		username=user["username"]

		if category=='all' and month=='all':
			query="""
			Match (u:User) where u.username={username}
			WITH point({latitude:u.latitude,longitude:u.longitude}) AS mapcenter
			MATCH (reco:Restaurant)-[:IN_DIVISION]->(d:Division) where d.e_name={location}
			WITH reco, distance (point({latitude: reco.latitude, longitude: reco.longitude}), mapcenter) AS distance
			RETURN reco, distance
			ORDER BY distance LIMIT 30
			"""
			return graph.data(query,username=username,location=location)

		if category!='all' and month=='all':
			query="""
			Match (u:User) where u.username={username}
			WITH point({latitude:u.latitude,longitude:u.longitude}) AS mapcenter
			MATCH (reco:Restaurant)-[:IN_DIVISION]->(d:Division),
			(reco)-[:IN_CATEGORY]->(c:Category)
			where d.e_name={location} and c.SDCategory={category}
			WITH reco, distance (point({latitude: reco.latitude, longitude: reco.longitude}), mapcenter) AS distance
			RETURN reco
			ORDER BY distance LIMIT 30
			"""
			return graph.data(query,username=username,location=location,category=category)

		


	def getDivision():
		query="""
			match (n:Division) return n.e_name as area
		"""
		return graph.data(query)

	def getCategory():
		query="""
			match (n:Category) return n.SDCategory as category
		"""
		return graph.data(query)

	def getMonth():
		query="""
			match (n:Month) return distinct n.month as month
		"""
		return graph.data(query)
##############################################################################################
def timestamp():
	epoch = datetime.utcfromtimestamp(0)
	now = datetime.now()
	delta = now - epoch
	return delta.total_seconds()
