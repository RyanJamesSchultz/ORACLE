% Simple script to examine the Weibull distribution, for the constraints of the data.
clear;

Tmean=2e+0;
shape=1.0;

scale=(Tmean/gamma(1+1/shape))^(-shape);

x=10.^(-10:0.01:+10);
lHF=log(scale)+log(shape)+(shape-1)*log(x);
lSVF=-scale*x.^shape;
lPDF=lHF+lSVF;
lCDF=log(1-exp(lSVF));
CHF=-lHF;

Tmean2=scale^(-1/shape)*gamma(1+1/shape);
Tmedian=exp(log(log(2)/scale)/shape);

Rmean=interp1(x,lHF,Tmean2,'linear','extrap');
Rmedian=interp1(x,lHF,Tmedian,'linear','extrap');

[Rmean -log(Tmean2)]
[Rmedian -log(Tmedian)]

figure(1); clf;
ax1=subplot(311);
semilogx(x,exp(lPDF)); hold on;
semilogx(Tmean2*[1 1],ylim(),':b');
semilogx(Tmedian*[1 1],ylim(),'--b');
xlabel('Inter-event time');
ylabel('PDF');
ax2=subplot(312);
semilogx(x,exp(lSVF),'DisplayName','SVF'); hold on;
semilogx(x,exp(lCDF),'DisplayName','CDF');
semilogx(Tmean2*[1 1],ylim(),':b','HandleVisibility','off');
semilogx(Tmedian*[1 1],ylim(),'--b','HandleVisibility','off');
xlabel('Inter-event time');
ylabel('SVF & CDF');
legend();
ax3=subplot(313);
semilogx(x,(lHF),'DisplayName','log HF'); hold on;
semilogx(x,(CHF),'DisplayName','CHF');
semilogx(Tmean2*[1 1],ylim(),':b','HandleVisibility','off');
semilogx(Tmedian*[1 1],ylim(),'--b','HandleVisibility','off');
semilogx([Tmean2,Tmedian],[Rmean,Rmedian],'ob','HandleVisibility','off');
xlabel('Inter-event time');
ylabel('log HF & CHF');
legend();

linkaxes([ax1 ax2 ax3],'x');



figure(2); clf;
ax1=subplot(211);
semilogx(x,x.^shape);
xlabel('Inter-event time');
ylabel('pow(x,shape)');
ax2=subplot(212);
semilogx(x,shape*x.^(shape-1));
xlabel('Inter-event time');
ylabel('dpow/dshape');
linkaxes([ax1 ax2],'x');

figure(3); clf;
b=0.1;
semilogy(-10:1e-2:10,log(1+exp(b*(-10:1e-2:10))/b)); hold on;
semilogy(-10:1e-2:10,exp(-10:1e-2:10));