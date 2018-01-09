from flask import Flask,request,session,redirect,url_for,render_template,flash
from .models import RecoEngine, User

app= Flask(__name__)
app.secret_key = "super secret key"

@app.route('/')
def index():
	# The index will show the search bar and current season recommmnendation, so we will render index with recommendation
	return render_template("index.html")
	
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 1:
            render_template("notice.html",message='Your username must be at least one character.')
        elif len(password) < 5:
            render_template("notice.html",message='Your password must be at least 5 characters.')
        elif not User(username).register(password):
            render_template("notice.html",message='A user with that username already exists.')
        else:
            session['username'] = username
            User(session['username']).setLocation()
            return render_template("notice.html",message='register sucessfully')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not User(username).verify_password(password):
            return render_template("notice.html",message='Invalid password')
        else:
            session['username'] = username
            User(session['username']).setLocation()
            return render_template("notice.html",message='Logged in.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template("notice.html",message='Log out.')
    
	
@app.route("/near_you",methods=["GET","POST"])
def near_you():
	if request.method== "POST":
		location=request.form["division"]
		recommendation=RecoEngine.res_near_you(location)
		return render_template("test_map.html",recommendation=recommendation,division=location)
	return render_template("near_you.html")

@app.route("/by_month",methods=["GET","POST"])
def by_month():
	if request.method== "POST":
		location=request.form["division"]
		month=request.form["month"]
		recommendation=RecoEngine.res_by_month(location,month)
		return render_template("show_by_month.html",recommendation=recommendation,division=location,month=month)
	return render_template("by_month.html")

@app.route("/general_rec",methods=["GET","POST"])
def general_rec():
	if request.method=="POST":
		location=request.form['division']
		category=request.form["category"]
		session["division"]=location
		session["category"]=category
		recommendation=RecoEngine.res_general_rec(location,category)
		return render_template("show_general_rec.html",recommendation=recommendation,division=location,category=category)
	return render_template("general_rec.html")

@app.route("/show_similiar_search",methods=["GET"])
def show_similiar_search():
	location=session["division"]
	category=session["category"]
	recommendation=RecoEngine.res_similiar_search(location, category)
	return render_template("show_similiar_rec.html",recommendation=recommendation,division=location,category=category)

@app.route("/show_relating_search",methods=["GET"])
def show_relating_search():
	location=session["division"]
	category=session["category"]
	recommendation=RecoEngine.res_relating_search(location,category)
	return render_template("show_relating_rec.html",recommendation=recommendation,division=location,category=category)

#new stuuff herere........
#new stufff hererewqwq..........
@app.route("/general_rec1",methods=["GET","POST"])
def general_rec1():
	if request.method=="POST":
		location=request.form['division']
		category=request.form["category"]
		month=request.form["month"]
		recommendation=RecoEngine.res_general_rec1(location,category,month)
		
		#save the search interest
		#a=User(session['username']).search_interest(recommendation)
		
		#have to do the engine twice coz cursor data lost,don't know other way yet
		recommendation1=RecoEngine.res_general_rec1(location,category,month)
		
		return render_template("show_general_rec.html",recommendation=recommendation1,division=location,category=category,month=month)
	return render_template("general_rec1.html")

@app.route("/show_similiar_search1",methods=["GET"])
def show_similiar_search1():
	recommendation=RecoEngine.res_similiar_search1(User(session['username']))
	return render_template("show_similiar_rec.html",recommendation=recommendation)


@app.route("/show_relating_search1",methods=["GET"])
def show_relating_search1():
	recommendation=RecoEngine.res_relating_search1(User(session['username']))
	return render_template("show_relating_rec.html",recommendation=recommendation)

#################updated after report##################################################################
@app.route("/by_this_month",methods=["GET","POST"])
def by_this_month():
	if request.method== "POST":
		location=request.form["division"]
		category=request.form["category"]
		user=User(session['username'])

		recommendation=RecoEngine.res_this_month(location,category,user)
		return render_template("show_by_month.html",recommendation=recommendation,division=location)
	return render_template("by_this_month.html")


@app.route("/more",methods=["GET","POST"])
def more():
	if request.method== "POST":
		location=request.form["division"]
		category=request.form["category"]
		month=request.form["month"]
		user=User(session['username'])
		
		recommendation=RecoEngine.more(location,category,month,user)
		return render_template("more.html",recommendation=recommendation)
	return render_template("general_rec2.html")

@app.route("/just_for_you",methods=["GET"])
def just_for_you():
	user=User(session['username'])
	recommendation=RecoEngine.near_you2(user)
	return render_template("just_for_you.html",near_you=recommendation)

######################################################################################################################################################
@app.route("/show",methods=["GET","POST"])
def show():
	if request.method=="POST":
		location=request.form["division"]
		category=request.form["category"]
		month=request.form["month"]
		user=User(session['username'])
		recommendation=RecoEngine.more2(location,category,month,user)
		if len(recommendation)>0:
			session['item']=recommendation[0]['reco']
		#reco=RecoEngine.more2(location,category,month,user)
		return render_template("show_reco.html",recommendation=recommendation)

	season=RecoEngine.currentSeason()
	category=RecoEngine.getCategory()
	month=RecoEngine.getMonth()
	division=RecoEngine.getDivision()
	topPlace=RecoEngine.topPlace()
	jiaoxi=RecoEngine.topResJiaoxi()
	yilan=RecoEngine.topRes("宜蘭市")
	loudong=RecoEngine.topRes("羅東鎮")
	toucheng=RecoEngine.topResToucheng()
	dongshan=RecoEngine.topResDongshan()
	return render_template("show.html",season=season,category=category,month=month,division=division,jiaoxi=jiaoxi,popular=topPlace,yilan=yilan,loudong=loudong,toucheng=toucheng,dongshan=dongshan)


@app.route("/res_detail/<shopId>")
def res_detail(shopId):
	###list shop detail and relating restaurant
	detail=RecoEngine.getDetail(shopId)
	reviews=RecoEngine.getReviews(shopId)
	relating=RecoEngine.relating(shopId)
	return render_template("res_detail.html",relating=relating,detail=detail,reviews=reviews)



