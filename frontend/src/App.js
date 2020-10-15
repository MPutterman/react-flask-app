import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import Button from '@material-ui/core/Button';
import Slider from '@material-ui/core/Slider';
import { palette } from '@material-ui/system';
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles';
import blueGrey from '@material-ui/core/colors/blueGrey';
import CssBaseline from '@material-ui/core/CssBaseline';
import { makeStyles } from '@material-ui/core/styles';
import Table from '@material-ui/core/Table';
import TableBody from '@material-ui/core/TableBody';
import TableCell from '@material-ui/core/TableCell';
import TableContainer from '@material-ui/core/TableContainer';
import TableHead from '@material-ui/core/TableHead';
import TableRow from '@material-ui/core/TableRow';
import Paper from '@material-ui/core/Paper';
import Typography from '@material-ui/core/Typography';
import { PassThrough } from 'stream';
import { thisExpression } from '@babel/types';


class App extends React.Component{
  constructor(props){
    
    super(props)
      this.darkReference = React.createRef();
      this.flatReference = React.createRef();
      this.cerenkovReference = React.createRef();
      this.UVReference = React.createRef();
      this.UVFlatReference = React.createRef();
      this.brightReference = React.createRef();
      this.brightFlatReference = React.createRef();
      this.theme = createMuiTheme({
      palette: {
        type:'dark',
        primary: {
          light: blueGrey[500],
          main: blueGrey[800],
          dark: blueGrey[900],
          contrastText: '#fff',
        },
        
        secondary: {
          light: '#ff7961',
          main: blueGrey[700],
          dark: '#002884',
          contrastText: '#000',
        },
      },
    });
    this.rads = [];
    this.origins = []
    this.ROIs = []
    this.filenum = ''
    this.ret=[]
    this.submit = this.submit.bind(this)
    this.clearOrigins = this.clearOrigins.bind(this)
    this.clearROIs=this.clearROIs.bind(this)
    this.removeROI=this.removeROI.bind(this);
    this.removeOrigin = this.removeOrigin.bind(this);
    this.state = {n_l:0,autoLane:true,submitted:false,UVImg:0,dataName:'',doRF:'Enable RF Calculation',CerenkovImg:0,brightness:0,contrast:0,show_us:'About Us',start:false,Darkname:'',Flatname:'',Cerenkovname:'',Brightname:'',BrightFlatname:'',UVname:'',UVFlatname:'',dataUploaded:false,resultsReturned:false,results:[],makeUpdate:0,doROIs:false,Dark:null,Flat:null,Cerenkov:null,UV:null,UVFlat:null,Bright:null,BrightFlat:null,ImgReturned:false,img:0};
    
     
  }
  
  
  makeData = arr=>{
    arr = Object.assign({},arr)
    return(arr)

  }
  calculate_vh = px=>{
    var vh=window.innerHeight/100
    return(px/vh)

  }
  calculate_vw = px=>{
    var vw = window.innerWidth/100
    return px/vw
  }
  UVClick=e=>{
    var x = e.nativeEvent.offsetX
    var y=e.nativeEvent.offsetY
    x = this.calculate_vw(x)/.19
    y=this.calculate_vh(y)/.3
    x = parseInt(6.82*x)
    y= parseInt(6.82*y)
    var shift = e.shiftKey ? 1:0
    console.log(shift)
    if (!this.state.doROIs){
      this.origins.push([x,y])
      this.setState({makeUpdate:1})
      

    }

    else{
      return axios.get(`http://54.151.59.130:5000//radius/`+this.filenum+`/`+x+`/`+y+`/`+shift)
  .then(res => {
    
    this.ROIs.push([res.data.col,res.data.row,res.data.rowRadius,res.data.colRadius]);
    this.setState({makeUpdate:8});
      return res
  });


    }
  }
  onReturnProcessed = res =>{
    this.filenum = res.data.res
    this.setState({img:`http://54.151.59.130:5000/img/`+res.data.res});
    this.setState({UVImg:`http://54.151.59.130:5000/UV/`+res.data.res});
    this.setState({CerenkovImg:`http://54.151.59.130:5000/Cerenkov/`+res.data.res});
    this.setState({ImgReturned:true});
    console.log(res.data)
    this.ROIs = res.data.test_ROIS
    this.setState({makeUpdate:109})
    console.log(this.ROIs)
    
    
  }
  componentDidMount(){
    window.addEventListener("keydown",this.changeROIFromPress)
  }
  changeROIFromPress = e=>{
    if (this.state.ImgReturned && !this.state.resultsReturned && this.ROIs.length>0){
      if (e.key =='w'){ 
        this.incVert()
	this.backVert()
        
      }
      if (e.key=='W'){
	this.decVert()
	this.backVert()
	      
      }

      if (e.key=='D'){
	this.moveHorz()
	this.decHorz()
      }
      if (e.key=='S'){
	this.decVert()
	this.moveVert()
      }   
      if (e.key=='A'){
	this.decHorz()
	this.backHorz()
      }
      if (e.key == 's'){
        this.incVert()
	this.moveVert()

      }
      if (e.key=='d'){
        this.incHorz()
	this.moveHorz()

      }
      if (e.key=='a'){
        this.incHorz()
	this.backHorz()

      }

    }
  }
  moveVert(){
	  var last = this.ROIs.length-1
	  if (this.ROIs[last][1]+4+this.ROIs[last][2]<682){
		this.ROIs[last][1]+=4
		this.setState({makeUpdate:10})
	  }

  }
  moveHorz(){
	var last = this.ROIs.length-1
	if (this.ROIs[last][0]+4+this.ROIs[last][3]<682){
		this.ROIs[last][0]+=4
		this.setState({makeUpdate:8})
	}
  }
  backHorz(){
	var last = this.ROIs.length-1
	if (this.ROIs[last][0]-4-this.ROIs[last][3]>0){
		this.ROIs[last][0]-=4
		this.setState({makeUpdate:10})
	}
  }
  backVert(){
	var last = this.ROIs.length-1
	if (this.ROIs[last][1]-4-this.ROIs[last][2]>0){
		this.ROIs[last][1]-=4
		this.setState({makeUpdate:10})
	}
  }
  
  submit(){
    let data = new FormData();
    data.append('ROIs',this.ROIs)
    data.append('origins',this.origins)
	  data.append('n_l',this.state.n_l)
    if (this.state.doRF == 'Disable RF Calculation'){
      data.append('doRF','true')
    }
    else{
      data.append('doRF','false')
    }
    console.log(this.state.autoLane)
    if(this.state.autoLane==true){
      data.append('autoLane','true')
    }
    else{
      data.append('autoLane','false')
    }
    return axios.post(`http://54.151.59.130:5000//results/`+this.filenum,data, {
      headers: {
          'Content-Type': 'multipart/form-data',
      },
      
  }).then(res=>{
    
    this.setState({results:res.data.arr,resultsReturned:true})
    

  })
  }
  _onMouseClick(e) {
    if (this.state.resultsReturned){
        return
    }
    this.setState({dataUploaded:false})
    if (!this.state.doROIs){
      this.origins.push([parseInt(e.nativeEvent.offsetX),parseInt(e.nativeEvent.offsetY)]);
      this.setState({makeUpdate:8})
    }
    else{
      var x = parseInt(e.nativeEvent.offsetX)
      var y = parseInt(e.nativeEvent.offsetY)
      var shift = e.shiftKey ? 1:0
      console.log(shift)
      return axios.get(`http://54.151.59.130:5000//radius/`+this.filenum+`/`+x+`/`+y+'/'+shift)
  .then(res => {
    
    this.ROIs.push([res.data.col,res.data.row,res.data.rowRadius,res.data.colRadius]);
    this.setState({makeUpdate:8});
      return res
  });

    }
  
  } 
  removeROI(e,i){
    if (this.state.resultsReturned){
        return
    }
 
     if (this.state.doROIs){
      this.ROIs.splice(i,1);
      this.setState({makeUpdate:9});
     }
	else{
		var x = e.nativeEvent.offsetX
		var y = e.nativeEvent.offsetY
		var radx = this.ROIs[i][3]
		var rady = this.ROIs[i][2]
		var px = this.ROIs[i][0]
		var py = this.ROIs[i][1]
		console.log(x,y,radx,rady,px,py)
		console.log(e.nativeEvent.offsetX,e.nativeEvent.offsetY)
		x = px-radx+x+7.5
		y=py-rady+y+7.5
		this.origins.push([parseInt(x),parseInt(y)])
		this.setState({makeUpdate:10})

	
	}
  }
  clearROIs(){
    this.ROIs.splice(0,this.ROIs.length)
    this.setState({makeUpdate:8})
  }
  clearOrigins(){
    this.origins.splice(0,this.origins.length)
    this.setState({makeUpdate:10})
  }

  removeOrigin(e,i){
    if (this.state.resultsReturned){
	return
    }
    if (!this.state.doROIs){
   	 this.origins.splice(i,1);
   	 this.setState({makeUpdate:19});
  }
   else{
	var x = e.nativeEvent.offsetX
	var y = e.nativeEvent.offsetY
	var radx = 12
	var rady = 12
	var px = this.origins[i][0]
	var py = this.origins[i][1]
	x=px-radx+x
	y=py-rady+y
	x = parseInt(x)
	y= parseInt(y)
      	var shift = e.shiftKey ? 1:0
      	console.log(shift)
      	return axios.get(`http://54.151.59.130:5000//radius/`+this.filenum+`/`+x+`/`+y+'/'+shift)
  	.then(res => {

    	this.ROIs.push([res.data.col,res.data.row,res.data.rowRadius,res.data.colRadius]);
    	this.setState({makeUpdate:8});
      	return res
  	});



   }
  }

    
  
  changeDoROIs=()=>{
    if (this.state.doROIs){
      this.setState({doROIs:false});
    }
    else{
      this.setState({doROIs:true});
    }
  }
  incVert=()=>{
    var last = this.ROIs.length-1;
    if ((this.ROIs[last][1]+this.ROIs[last][2]<682-4) && (this.ROIs[last][1]-this.ROIs[last][2]>4)){
    this.ROIs[last][2]+=4;
    this.setState({makeUpdate:12})
  }}
  incHorz=()=>{
    var last = this.ROIs.length-1;
    if ((this.ROIs[last][0]+this.ROIs[last][3]<682-4) && (this.ROIs[last][0]-this.ROIs[last][3]>4)){
    this.ROIs[last][3]+=4;
    this.setState({makeUpdate:12})
  }}
  decHorz=()=>{
    var last = this.ROIs.length-1;
    if (this.ROIs[last][3]>14){
    this.ROIs[last][3]-=4;
    this.setState({makeUpdate:12})
  }}
  decVert=()=>{
    var last = this.ROIs.length-1;
    if (this.ROIs[last][2]>14){
    this.ROIs[last][2]-=4;
    this.setState({makeUpdate:12})
  }}
  add_data=()=>{

	this.setState({dataUploaded:true})
	let data = new FormData();
	for (var key in this.state){
		data.append(key,this.state[key])
	}
	data.append('ROIs',this.ROIs)
	data.append('origins',this.origins)
	data.append('filenum',this.filenum)
	  return axios.post(`http://54.151.59.130:5000/database`,data,
		{headers:{'Content-Type':'multipart/form-data',},})
  }
  
  onFileUpload =()=>{
    this.setState({submitted:true})
    let data = new FormData();
    const fileblob1 = new Blob([this.state.Dark], { type: 'image/png' });
    data.append("Dark", fileblob1 );
    const fileblob2 = new Blob([this.state.Flat], { type: 'image/png' });
    data.append("Flat", fileblob2 );
    const fileblob3 = new Blob([this.state.UVFlat], { type: 'image/png' });
    data.append("UVFlat", fileblob3 );
    const fileblob4 = new Blob([this.state.UV], { type: 'image/png' });
    data.append("UV", fileblob4 );
    const fileblob5 = new Blob([this.state.Cerenkov], { type: 'image/png' });
    data.append("Cerenkov", fileblob5 );
    const fileblob6 = new Blob([this.state.Bright], { type: 'image/png' });
    data.append("Bright", fileblob6 );
    const fileblob7 = new Blob([this.state.BrightFlat], { type: 'image/png' });
    data.append("BrightFlat", fileblob7 );
    return axios
        .post(`http://54.151.59.130:5000/time`, data, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        })
        .then(res => {
          
          this.onReturnProcessed(res);
          return res
    });
  }
  
  render(){
    
    return(
      <ThemeProvider theme={this.theme}>
        <CssBaseline/>
      <div id = 'container'>
        {this.state.resultsReturned &&
          <Button color = 'primary' variant='contained'style = {{fontSize:"160%",height:'12vh',width:'12vw',position:'absolute',marginTop:'87vh',marginLeft:'87vw'}} onClick = {()=>{this.setState({resultsReturned:false})}}>Reselect</Button>}
	{this.state.resultsReturned && !this.state.dataUploaded&&
	<Button color = 'primary' variant = 'contained' style = {{fontSize:'100%',height:'12vh',width:'12vw',position:'absolute',marginTop:'87vh',marginLeft:'682px'}}onClick = {this.add_data}>Upload to Database</Button>}
        {this.state.resultsReturned==true &&
         <TableContainer  component={Paper}>
         <Table style = {{textAlign:'center',marginTop:'0vh',marginLeft:"682px",zIndex:15,alignContent:'center',height:''+(this.state.results.length*19)+'vh',width:''+(this.state.results[0].length*4.6)+'vw',position:'absolute'}} size="medium" aria-label="a dense table">
           <TableHead>
           
             <TableRow style={{textAlign:'center',height:'7vh'}}>
               <TableCell id='tc'padding = 'checkbox' style = {{textAlign:'center', height: 'auto !important',fontSize:'160%'}} >ROIS</TableCell>
               {this.state.results[0].map((spot, i)=>{
                return <TableCell id = 'tc' style = {{fontSize:'140%', textAlign:'center', alignContent:'center'}} padding = 'checkbox' key = {i} align="right">L{i+1} </TableCell>
              })}
             </TableRow>
           
           </TableHead>
           <TableBody>
             {this.state.results.map((lane,i) => {
               return(
               <TableRow key={i}>
                 <TableCell id = 'tc' padding = 'checkbox' style = {{fontSize:'110%', height: 'auto !important'}} component="th" scope="row">
                   Spot {i+1}
                 </TableCell>
                 {lane.map((spot,j)=>{
                 return <TableCell id='tc' padding = 'checkbox' style = {{fontSize:'130%', height: 'auto !important'}} key = {j} align="right">{parseInt(spot[0]*100)}% {spot.length>1 ?  " " + spot[1]:""}</TableCell>
                 })}
                 
                
               </TableRow>
    );})}
           </TableBody>
         </Table>
       </TableContainer>
        }
        {this.state.start==false&&
        <div>
        <Button style = {{fontSize:'5vh',position:'absolute',marginTop:'0vh',marginLeft:'0vh',width:'100vw',height:'10vh',backgroundColor: blueGrey[900]}} onClick = {()=>{this.state.show_us == '' ?this.setState({show_us:"About Us"}): this.setState({show_us:''})}}>{this.state.show_us}</Button>
        <img style = {{position:'absolute',marginTop:'30vh',marginLeft:'25vw',width:'15vw',height:'10vh'}} src = {process.env.PUBLIC_URL + '/logo_UCLA_blue_boxed.png'} />
        <h1 style = {{fontSize :'6vh',position:'absolute',marginTop:'28vh',marginLeft:'41vw',width:'50vw',height:'10vh'}}>van Dam Lab</h1>
        <h1 style = {{position:'absolute',marginTop:'36.5vh',marginLeft:'41vw',width:'70vw',height:'10vh',fontSize:'2.5vh'}}>Calculate RF values and Cerenkov Ratios of radio TLC images Quickly</h1>
        <Button style = {{fontSize:'2.5vh',position:'absolute',marginTop:'44vh',marginLeft:'41vw',width:'10vw',height:'10vh'}}variant = 'contained' color = 'primary' onClick = {()=>{this.setState({start:true})}}>Get Started</Button>
        </div>
        }
        {this.ROIs.map((x, i)=>{
          return <h1  key = {i} style = {{position:'absolute', backgroundColor:"transparent", zIndex:this.state.doROIs ? 11:10, borderRadius:'50%/50%',border:"solid 5px #f00",width:""+2*x[3]-5+'px',height:""+2*x[2]-5+'px',marginTop:""+x[1]-1*x[2]+2.5+'px',marginLeft:""+x[0]-1*x[3]+2.5+'px'}} onClick = {e => {e.preventDefault();this.removeROI(e,i)}}/>
          
           // return <view id="circle" key = {x} style= {{width:x[2],height:x[3],top:x[1],left:x[0]}}/>
        })}
        {this.origins.map((x,i)=>{
          return <h1 key = {i} style = {{borderRadius:'50%/50%',backgroundColor:'white',position:'absolute',marginTop:''+1*x[1]-12+'px',marginLeft:''+1*x[0]-12+'px',width:'24px',height:'24px',zIndex:this.state.doROIs ? 10:11}} onClick = {e => {e.preventDefault();this.removeOrigin(e,i)}}/>
        }
        
        )}
        {this.state.ImgReturned &&
        <img id="img" style = {{position:'absolute',filter:'brightness(10)',filter:'contrast('+(100+10*this.state.contrast)+'%)'}}src={(this.state.img)} onClick = {this._onMouseClick.bind(this)} />}
        
        {!this.state.resultsReturned &&
        <div>
        {this.state.ImgReturned && (this.state.UVname!='' || this.state.Brightname!='')&&
        <div>
          <h1 style = {{position:'absolute',marginTop:'30vh',marginLeft:'60vw',height:'30vh',width:'20vw'}} >epic!</h1>
          <img src ={this.state.UVImg}  style = {{position:'absolute',marginTop:'30vh',marginLeft:'56vw',height:'30vh',width:'19vw',filter:'contrast('+(100+10*this.state.contrast)+'%)'}} onClick={this.UVClick}/>
          <img src ={this.state.CerenkovImg}  style = {{position:'absolute',marginTop:'30vh',marginLeft:'77vw',height:'30vh',width:'19vw',filter:'contrast('+(100+10*this.state.contrast)+'%)'}} onClick={this.UVClick}/>


        </div>
        
        }
        {this.state.ImgReturned && (this.state.UVname=='' && this.state.Brightname=='')&&
      <Button color = "primary" variant = 'contained' style ={{fontSize:"120%",height:'12vh',width:'12vw',position:'absolute',marginTop:'40vh',marginLeft:'60vw'}} onClick = {()=>{this.state.doRF =='Enable RF Calculation' ? this.setState({doRF:'Disable RF Calculation'}):this.setState({doRF:'Enable RF Calculation'})}}>{this.state.doRF}</Button>
      }
      {this.state.ImgReturned && (this.state.UVname=='' && this.state.Brightname=='')&&
      <Button color = "primary" variant = 'contained' style ={{fontSize:"100%",height:'12vh',width:'12vw',position:'absolute',marginTop:'40vh',marginLeft:'80vw'}} onClick={()=>{console.log(this.state.autoLane);this.setState({autoLane:!this.state.autoLane})}}> {!this.state.autoLane ? "Enable Auto Lane Select" :"Enable Manual Lane Select"} </Button>
      }
	{this.state.ImgReturned&&(this.state.UVname==''&&this.state.Brightname=='')&&this.state.autoLane&&
			<div>
			<Slider valueLabelDisplay="auto" style = {{position:'absolute',height:'7vh',width:'12vw',marginTop:'57vh',marginLeft:'80vw'}} step={1} marks={true} defaultValue = {this.state.n_l} min = {0} max = {10} onChange={(e,val)=>{this.setState({n_l:val})}}/>
	<h1 style = {{position:'absolute',height:'8vh',width:'8vh',fontSize:'90%',marginTop:'54vh',marginLeft:'84vw'}}>#Lanes</h1>
			</div>
	}
        {this.state.ImgReturned &&
        
        <Slider  valueLabelDisplay="auto"  style = {{position:'absolute',height:'8vh',width:'32vw',marginTop:'3vh',marginLeft:'60vw'}} step = {3} marks = {true} defaultValue = {this.state.contrast} min = {-9} max = {21}onChange={(e,value)=>{this.setState({contrast:value})}}>Contrast</Slider>}
        {this.state.ImgReturned &&
        <h1 style = {{position:'absolute',height:'2vh',width:'10vw',marginTop:'0vh',marginLeft:'76vw'}}>Contrast</h1>
        }
        {this.state.ImgReturned &&
        <Button color = 'primary' variant='contained'style = {{fontSize:"190%",height:'12vh',width:'12vw',position:'absolute',marginTop:'70vh',marginLeft:'80vw'}} onClick = {this.submit}>Submit</Button>}
        {this.state.ImgReturned &&
        <Button color = 'primary' variant='contained' style = {{fontSize:"90%",position:'absolute',height:'12vh',width:'12vw',marginTop:'70vh',marginLeft:'60vw'}} id = 'Button'onClick = {this.changeDoROIs}>{!this.state.doROIs ? "Select ROIs" : "Select Origin/SF/Cerenkov Lanes"}</Button>}
        {this.state.ImgReturned &&
        <p id = "circle"/>}
        {this.state.ImgReturned &&
        <Button color = 'primary' variant='contained' style = {{fontSize:"170%",height:'12vh',width:'12vw',position:'absolute',marginTop:'10vh',marginLeft:'80vw'}} onClick = {this.clearROIs}>Clear ROIs</Button>}
        {this.state.ImgReturned &&
        <Button color = 'primary' variant='contained' style = {{fontSize:"170%",height:'12vh',width:'12vw',position:'absolute',marginTop:'10vh',marginLeft:'60vw'}} onClick = {this.clearOrigins}>Clear Origins</Button>}
        </div>}
        
        {this.state.start ==true &&
        <div>
          {this.state.ImgReturned == false && this.state.submitted==false&&
        <Button color = 'primary' variant="contained" style = {{fontSize:'2.5vh',position:'absolute',marginTop:'80vh',marginLeft:'80vw',width:'20vw',height:'20vh'}}onClick = {this.onFileUpload}>Submit</Button>
        }
        {this.state.ImgReturned == false &&
        <input type="file" hidden ref={this.UVFlatReference} onChange={e=>{this.setState({UVFlatname:e.target.value.substr(e.target.value.indexOf("FAKEPATH/")+13),UVFlat:e.target.files[0]})}} />
        }
        {this.state.ImgReturned == false &&
        <Button color = 'primary' variant = "contained" style = {{fontSize:'2vh',position:'absolute',marginTop:'45vh',marginLeft:'40vw',width:'20vw',height:'20vh'}} onClick={()=>this.UVFlatReference.current.click()}>
            UV Flatfield Upload (optional): {this.state.UVFlatname}
        </Button>
        }

        {this.state.ImgReturned == false &&
        <input type="file" hidden ref={this.UVReference}  onChange={e=>{this.setState({UVname:(e.target.value).substr(e.target.value.indexOf("FAKEPATH/")+13),UV:e.target.files[0]})}} />
        }
        {this.state.ImgReturned == false &&
        <Button style = {{fontSize:'2.5vh',position:'absolute',marginTop:'20vh',marginLeft:'40vw',width:'20vw',height:'20vh'}} color = 'primary' variant = "contained"  onClick={()=>this.UVReference.current.click()}>
            UV Upload (optional): {this.state.UVname}
        </Button>
        }

        {this.state.ImgReturned == false &&
        <input type="file" hidden ref={this.brightFlatReference} onChange={e=>{this.setState({brightFlatname:e.target.value.substr(e.target.value.indexOf("FAKEPATH/")+13),BrightFlat:e.target.files[0]})}} />
        }
        {this.state.ImgReturned == false &&
        <Button color = 'primary' variant = "contained"  style = {{fontSize:'2vh',position:'absolute',marginTop:'45vh',marginLeft:'70vw',width:'20vw',height:'20vh'}} onClick={()=>this.brightFlatReference.current.click()}>
            Bright Flatfield Upload (optional): {this.state.brightFlatname}
        </Button>
        }
        {this.state.ImgReturned == false && this.state.submitted==false&&
        <Button color = 'primary' variant = 'contained' style = {{fontSize:'2vh',position:'absolute',marginTop:'70vh',marginLeft:'40vw',width:'20vw',height:'20vh'}} onClick = {this.onFileUpload} >Use Sample Data</Button>
        }

        {this.state.ImgReturned == false &&
        <h1 style = {{fontSize:'3.5vh',textAlign:'center',position:'absolute',marginTop:'0vh',marginLeft:'0vw',width:'100vw',height:'10vh',backgroundColor:blueGrey[900]}}>Click on the buttons to select a file. To run the code, you will need a Cerenkov image. Accepts greyscale png, txt, tiff.</h1>}

        {this.state.ImgReturned == false &&
        <input type="file" hidden ref={this.brightReference} onChange={e=>{this.setState({Brightname:e.target.value.substr(e.target.value.indexOf("FAKEPATH/")+13),Bright:e.target.files[0]})}} />
        }
        {this.state.ImgReturned == false &&
        <Button color = 'primary' style = {{fontSize:'2vh',position:'absolute',marginTop:'20vh',marginLeft:'70vw',width:'20vw',height:'20vh'}} variant = "contained"  onClick={()=>this.brightReference.current.click()}>
            Brightfield Upload (optional): {this.state.Brightname}
        </Button>
        }

        {this.state.ImgReturned == false &&
        <input type="file" hidden ref={this.cerenkovReference} onChange={e=>{this.setState({Cerenkovname:e.target.value.substr(e.target.value.indexOf("FAKEPATH/")+13),Cerenkov:e.target.files[0]})}} />
        }
        {this.state.ImgReturned == false &&
        <Button style = {{fontSize:'2.5vh',position:'absolute',marginTop:'20vh',marginLeft:'10vw',width:'20vw',height:'20vh'}} color = 'primary' variant = "contained"  onClick={()=>this.cerenkovReference.current.click()}>
            Cerenkov Upload: {this.state.Cerenkovname}
        </Button>
        }

        {this.state.ImgReturned == false &&
        <input type="file" hidden ref={this.flatReference} onChange={e=>{this.setState({Flatname:e.target.value.substr(e.target.value.indexOf("FAKEPATH/")+13),Flat:e.target.files[0]})}} />
        }
        {this.state.ImgReturned == false &&
        <Button style = {{fontSize:'2.3vh',position:'absolute',marginTop:'45vh',marginLeft:'10vw',width:'20vw',height:'20vh'}} color = 'primary' variant = "contained"  onClick={()=>this.flatReference.current.click()}>
            Flatfield Upload (optional): {this.state.Flatname}
        </Button>
        }

        {this.state.ImgReturned == false &&
        <input type="file" hidden ref={this.darkReference} onChange={e=>{this.setState({Darkname:e.target.value.substr(e.target.value.indexOf("FAKEPATH/")+13),Dark:e.target.files[0]})}} />
        }
        {this.state.ImgReturned == false &&
        <Button style = {{fontSize:'2.3vh',position:'absolute',marginTop:'70vh',marginLeft:'10vw',width:'20vw',height:'20vh'}} color = 'primary' variant = "contained"  onClick={()=>this.darkReference.current.click()}>
            Darkfield Upload (optional): {this.state.Darkname}
        </Button>
        }
        </div>}
      </div>
      </ThemeProvider>
    );

  }

}
export default App;

