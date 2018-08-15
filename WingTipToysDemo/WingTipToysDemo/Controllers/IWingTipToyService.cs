using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using WingTipToysEntities;

namespace WingTipToysDemo.Controllers
{
    public interface IWingTipToyService
    {
        Task<IEnumerable<ToyDetailsViewModel>> GetToyList ( );
    }
}