let photos = ["/static/img/1.jpg","/static/img/2.jpg","/static/img/3.jpg"]



i = 0
next.onclick=function(){
    if (i <= photos.length-1){
        sliderPhoto.src=photos[i]
        i+=1
    }
    else if (i==photos.length){
        i=0
        sliderPhoto.src=photos[i]
        i+=1
        
    }
}

setInterval(next, 3000);

previous.onclick=function(){
    i-=1
    if (i<=0)
        {i=photos.length
            sliderPhoto.src=photos[0]}
    else
        {sliderPhoto.src=photos[i]}}